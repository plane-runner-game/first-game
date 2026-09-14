// AudioManager.cs
// Sound effects synthesized in code at startup (no audio files needed yet). Each Sfx is
// a tiny recipe: a tone sweep, a noise burst, or a few notes. Swap for real clips later
// by assigning AudioClips in the overrides array.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public enum Sfx { Good, Big, Bad, Gun, Rocket, Laser, Unit, Explode, Boom, Flak, Pop, Pickup, ShieldHit, Warn, Lose, Clear, Over, Tick }

    public class AudioManager : MonoBehaviour
    {
        public static AudioManager I { get; private set; }

        [Serializable] public class Override { public Sfx sfx; public AudioClip clip; }
        public Override[] overrides;
        public int voices = 10;

        const int SR = 22050;
        readonly Dictionary<Sfx, AudioClip> clips = new Dictionary<Sfx, AudioClip>();
        readonly Dictionary<Sfx, float> lastPlay = new Dictionary<Sfx, float>();
        AudioSource[] sources;
        int next;
        bool muted;

        public bool Muted { get => muted; set { muted = value; PlayerPrefs.SetInt("sky_mute", value ? 1 : 0); } }

        void Awake()
        {
            I = this;
            muted = PlayerPrefs.GetInt("sky_mute", 0) == 1;
            sources = new AudioSource[voices];
            for (int i = 0; i < voices; i++) { sources[i] = gameObject.AddComponent<AudioSource>(); sources[i].playOnAwake = false; sources[i].spatialBlend = 0f; }
            BuildClips();
            if (overrides != null) foreach (var o in overrides) if (o.clip != null) clips[o.sfx] = o.clip;
        }

        public void Play(Sfx s)
        {
            if (muted || !clips.TryGetValue(s, out var clip)) return;
            float gate = s == Sfx.Gun ? 0.05f : s == Sfx.Laser ? 0.09f : s == Sfx.Unit ? 0.06f : 0f;
            if (gate > 0f) { if (lastPlay.TryGetValue(s, out float t) && Time.time - t < gate) return; lastPlay[s] = Time.time; }
            var src = sources[next]; next = (next + 1) % sources.Length;
            src.pitch = s == Sfx.Gun || s == Sfx.Unit ? UnityEngine.Random.Range(0.92f, 1.08f) : 1f;
            src.PlayOneShot(clip, 1f);
        }

        // ---- tiny synth -------------------------------------------------------
        class Buf
        {
            public float[] s; public Buf(float seconds) { s = new float[(int)(SR * seconds) + 1]; }
            public void Tone(float f0, float f1, float dur, string wave, float vol, float delay = 0f)
            {
                int start = (int)(delay * SR), n = (int)(dur * SR); double phase = 0;
                for (int i = 0; i < n && start + i < s.Length; i++)
                {
                    float k = i / (float)n;
                    float f = f0 * Mathf.Pow(Mathf.Max(1f, f1) / f0, k);
                    phase += f / SR;
                    float env = vol * Mathf.Exp(-7f * k);
                    double p = phase - Math.Floor(phase);
                    float v = wave == "square" ? (p < 0.5 ? 1f : -1f) : wave == "saw" ? (float)(2 * p - 1) : wave == "tri" ? (float)(4 * Math.Abs(p - 0.5) - 1) : (float)Math.Sin(p * Math.PI * 2);
                    s[start + i] += v * env;
                }
            }
            public void Noise(float dur, float vol, float cutoff, float delay = 0f)
            {
                int start = (int)(delay * SR), n = (int)(dur * SR);
                float a = 1f - Mathf.Exp(-2f * Mathf.PI * cutoff / SR), y = 0f;
                var rng = new System.Random(7);
                for (int i = 0; i < n && start + i < s.Length; i++)
                {
                    float k = i / (float)n;
                    float x = (float)(rng.NextDouble() * 2 - 1);
                    y += a * (x - y);
                    s[start + i] += y * vol * Mathf.Exp(-6f * k) * 3f;
                }
            }
            public AudioClip Clip(string name)
            {
                float peak = 0f; foreach (var v in s) peak = Mathf.Max(peak, Mathf.Abs(v));
                if (peak > 1f) for (int i = 0; i < s.Length; i++) s[i] /= peak;
                var c = AudioClip.Create(name, s.Length, 1, SR, false);
                c.SetData(s, 0);
                return c;
            }
        }

        void BuildClips()
        {
            Buf b;
            b = new Buf(0.3f); b.Tone(660, 1320, 0.14f, "square", 0.14f); b.Tone(990, 1980, 0.14f, "sine", 0.12f, 0.06f); clips[Sfx.Good] = b.Clip("good");
            b = new Buf(0.45f); float[] big = { 660, 880, 1100, 1320 }; for (int i = 0; i < 4; i++) b.Tone(big[i], big[i], 0.12f, "square", 0.13f, i * 0.06f); clips[Sfx.Big] = b.Clip("big");
            b = new Buf(0.4f); b.Tone(200, 90, 0.35f, "saw", 0.26f); b.Tone(150, 70, 0.35f, "square", 0.12f); clips[Sfx.Bad] = b.Clip("bad");
            b = new Buf(0.06f); b.Tone(1600, 600, 0.04f, "square", 0.05f); clips[Sfx.Gun] = b.Clip("gun");
            b = new Buf(0.3f); b.Noise(0.25f, 0.3f, 1200); b.Tone(300, 90, 0.25f, "saw", 0.08f); clips[Sfx.Rocket] = b.Clip("rocket");
            b = new Buf(0.1f); b.Tone(1200, 1500, 0.08f, "sine", 0.06f); clips[Sfx.Laser] = b.Clip("laser");
            b = new Buf(0.09f); b.Tone(500, 200, 0.07f, "tri", 0.1f); clips[Sfx.Unit] = b.Clip("unit");
            b = new Buf(0.4f); b.Noise(0.35f, 0.5f, 700); b.Tone(160, 40, 0.3f, "saw", 0.18f); clips[Sfx.Explode] = b.Clip("explode");
            b = new Buf(0.9f); b.Noise(0.8f, 0.9f, 500); b.Tone(120, 30, 0.7f, "saw", 0.3f); clips[Sfx.Boom] = b.Clip("boom");
            b = new Buf(0.2f); b.Noise(0.15f, 0.45f, 600); b.Tone(120, 60, 0.15f, "square", 0.12f); clips[Sfx.Flak] = b.Clip("flak");
            b = new Buf(0.2f); b.Tone(800, 1600, 0.1f, "sine", 0.2f); b.Tone(1200, 2000, 0.1f, "tri", 0.12f, 0.05f); clips[Sfx.Pop] = b.Clip("pop");
            b = new Buf(0.35f); float[] pk = { 880, 1100, 1320, 1760 }; for (int i = 0; i < 4; i++) b.Tone(pk[i], pk[i], 0.1f, "tri", 0.14f, i * 0.05f); clips[Sfx.Pickup] = b.Clip("pickup");
            b = new Buf(0.2f); b.Tone(700, 300, 0.15f, "sine", 0.2f); clips[Sfx.ShieldHit] = b.Clip("shieldhit");
            b = new Buf(0.35f); b.Tone(220, 220, 0.12f, "square", 0.12f); b.Tone(220, 220, 0.12f, "square", 0.12f, 0.18f); clips[Sfx.Warn] = b.Clip("warn");
            b = new Buf(0.45f); b.Noise(0.4f, 0.5f, 700); b.Tone(400, 120, 0.4f, "saw", 0.2f); clips[Sfx.Lose] = b.Clip("lose");
            b = new Buf(0.6f); float[] cl = { 523, 659, 784, 1046, 1318 }; for (int i = 0; i < 5; i++) b.Tone(cl[i], cl[i], 0.18f, "square", 0.15f, i * 0.09f); clips[Sfx.Clear] = b.Clip("clear");
            b = new Buf(1.0f); float[] ov = { 440, 370, 311, 262 }; for (int i = 0; i < 4; i++) b.Tone(ov[i], ov[i] * 0.97f, 0.3f, "saw", 0.18f, i * 0.2f); clips[Sfx.Over] = b.Clip("over");
            b = new Buf(0.07f); b.Tone(900, 700, 0.05f, "square", 0.1f); clips[Sfx.Tick] = b.Clip("tick");
        }
    }
}
