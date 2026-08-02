"""beatlab.ears — machine listening: reference calibration + perceptual scoring.

Closes the "producing deaf" gap without human ears in the loop:
- fingerprint(): librosa DSP features that correlate with how a mix reads —
  spectral tilt, band balance, onset density, percussive ratio, dynamics,
  crest factor.
- RefBank: fingerprints of real commercial reference tracks (30s iTunes
  previews of the target corpus) -> mean/spread per feature.
- gap_report(): where a render deviates from the reference distribution.
- ClapCritic: LAION-CLAP audio-text model — scores renders against positive
  and negative text prompts and by cosine similarity to reference audio
  embeddings. A learned perceptual judge, not a rule.
"""
import glob
import os

import numpy as np
import librosa
import soundfile as sf

REF_DIR = os.environ.get(
    "BEATLAB_REFS",
    "/tmp/claude-0/-home-user-Beat/46e08380-25a6-5652-aa66-dd3b51c68911/scratchpad/refs")

BANDS = [(20, 60, "sub"), (60, 150, "bass"), (150, 500, "lowmid"),
         (500, 2000, "mid"), (2000, 6000, "presence"), (6000, 16000, "air")]


def fingerprint(path, max_s=32.0):
    y, sr = librosa.load(path, sr=44100, mono=True, duration=max_s)
    S = np.abs(librosa.stft(y, n_fft=4096)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
    total = S.sum() + 1e-12
    fp = {}
    for lo, hi, name in BANDS:
        m = (freqs >= lo) & (freqs < hi)
        fp[f"band_{name}"] = float(S[m].sum() / total)
    fp["centroid_hz"] = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    fp["rolloff_hz"] = float(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.9).mean())
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    fp["onsets_per_s"] = float(len(onsets) / (len(y) / sr))
    yh, yp = librosa.effects.hpss(y)
    fp["percussive_ratio"] = float((yp ** 2).sum() / ((yh ** 2).sum() + (yp ** 2).sum() + 1e-12))
    # dynamics: variance of short-term RMS (dB), and crest factor
    rms = librosa.feature.rms(y=y, frame_length=22050, hop_length=11025)[0]
    fp["dyn_range_db"] = float(np.percentile(20 * np.log10(rms + 1e-9), 95)
                               - np.percentile(20 * np.log10(rms + 1e-9), 20))
    fp["crest_db"] = float(20 * np.log10(np.abs(y).max() / (np.sqrt((y ** 2).mean()) + 1e-12)))
    fp["flatness"] = float(librosa.feature.spectral_flatness(y=y).mean())
    return fp


class RefBank:
    def __init__(self, ref_dir=REF_DIR):
        self.fps = {}
        for p in sorted(glob.glob(f"{ref_dir}/*.wav")):
            self.fps[os.path.basename(p)[:-4]] = fingerprint(p)
        keys = list(next(iter(self.fps.values())).keys())
        self.mean = {k: float(np.mean([f[k] for f in self.fps.values()])) for k in keys}
        self.std = {k: float(np.std([f[k] for f in self.fps.values()]) + 1e-9) for k in keys}

    def gap_report(self, path, threshold=1.3):
        """Features where the render sits > threshold sigma from the refs."""
        fp = fingerprint(path)
        gaps = []
        for k, v in fp.items():
            z = (v - self.mean[k]) / self.std[k]
            if abs(z) > threshold:
                gaps.append((k, v, self.mean[k], round(z, 2)))
        return fp, sorted(gaps, key=lambda g: -abs(g[3]))


class ClapCritic:
    POS = ["a professional hard-hitting hip hop trap beat with punchy 808 bass and crisp drums",
           "a dark modern rap instrumental, expensive studio production, wide and clear mix"]
    NEG = ["an amateur demo beat, muddy weak drums, thin cheap sounding mix",
           "low quality midi music, toy keyboard sounds"]

    def __init__(self):
        import laion_clap
        self.m = laion_clap.CLAP_Module(enable_fusion=False)
        self.m.load_ckpt(verbose=False)
        self.pos_e = self.m.get_text_embedding(self.POS, use_tensor=False)
        self.neg_e = self.m.get_text_embedding(self.NEG, use_tensor=False)
        self._ref_e = None

    def _embed(self, paths):
        return self.m.get_audio_embedding_from_filelist(x=paths, use_tensor=False)

    def ref_embeddings(self, ref_dir=REF_DIR):
        if self._ref_e is None:
            paths = sorted(glob.glob(f"{ref_dir}/*.wav"))
            self._ref_e = self._embed(paths).mean(axis=0, keepdims=True)
        return self._ref_e

    @staticmethod
    def _cos(a, b):
        a = a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-9)
        b = b / (np.linalg.norm(b, axis=-1, keepdims=True) + 1e-9)
        return a @ b.T

    def score(self, path):
        """Returns (pro_score, ref_similarity). pro_score = mean pos sim - mean neg sim."""
        e = self._embed([path])
        pro = float(self._cos(e, self.pos_e).mean() - self._cos(e, self.neg_e).mean())
        ref = float(self._cos(e, self.ref_embeddings()).mean())
        return pro, ref

    def rank(self, paths):
        rows = []
        for p in paths:
            pro, ref = self.score(p)
            rows.append((p, round(pro, 4), round(ref, 4)))
        return sorted(rows, key=lambda r: -(r[1] + r[2]))
