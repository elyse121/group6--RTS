import re
import sys

# (generation, problem class, keywords, justification) -- ordered earliest -> latest.
# A trailing * means "starts with" (stem match); everything else is a whole word/phrase.
RULES = [
    ("0G", "first vehicle radio-telephone",
     ["operator assisted", "push to talk", "pre cellular", "precellular", "radiotelephone",
      "radio telephone", "mobile telephone service", "imts", "mts", "vehicle radio", "car radio",
      "before cellular", "before cell towers", "manual connect*"],
     "0G (MTS 1946, IMTS 1964): the first vehicle radio-telephone, using a handful of shared channels "
     "and operator-assisted connection, with no cells or frequency reuse."),
    ("1G", "basic mobile voice with the cellular concept",
     ["analog*", "analogue*", "amps", "nmt", "tacs", "cellular concept", "frequency reuse", "handoff",
      "first cell phone", "first cellular", "phone call", "voice call", "make a call", "cell phone call",
      "walk and talk"],
     "1G (AMPS 1983, NMT 1981, NTT 1979): analog FM cellular. Cells and frequency reuse removed the "
     "0G capacity bottleneck, giving automatic mobile voice for many users."),
    ("2G", "secure, digital, roaming-capable voice and text",
     ["digital voice", "digital cellular", "encrypt*", "eavesdrop*", "listening in", "privacy", "secure call",
      "interception", "cloning", "sms", "text message", "texting", "sim", "sim card", "roaming", "roam*",
      "gsm", "interoperab*", "pan european", "voicemail", "abroad", "overseas", "foreign country",
      "calls private", "private calls"],
     "2G (GSM 1991): digital radio with encryption against eavesdropping, SMS, SIM-based subscriber "
     "identity and cross-border roaming, fixing 1G's insecurity and fragmentation."),
    ("2.5G", "packet-switched data (GPRS/EDGE)",
     ["packet*", "always on", "pay per volume", "per kilobyte", "gprs", "edge", "wap", "mms",
      "picture message", "photo message", "multimedia message", "bursty", "mobile email",
      "email on my phone", "circuit switched data", "dial up"],
     "2.5G (GPRS/EDGE): packet switching so bursty data no longer holds a circuit, with billing by "
     "volume and always-on connectivity; it proved packet data before 3G."),
    ("3G", "mobile broadband and multimedia",
     ["video call*", "video chat", "mobile broadband", "mobile web", "web browsing", "browse*", "website*",
      "web page*", "umts", "wcdma", "hspa", "imt 2000", "global standard", "multimedia", "mobile tv",
      "mobile internet", "internet on my phone", "3g"],
     "3G (UMTS/HSPA, ~2001+; IMT-2000): designed for data from the start, giving 144 kbps-2 Mbps "
     "rates on paper and, with HSPA, usable mobile web and video calls."),
    ("4G", "all-IP high-capacity broadband",
     ["lte", "4g", "all ip", "voip", "hd video", "high definition", "stream*", "hotspot", "tethering",
      "ride hailing", "navigation app", "social media", "video conferencing", "online gam*",
      "mobile gam*", "ofdma", "carrier aggregation", "gigabit"],
     "4G (LTE/LTE-Advanced; IMT-Advanced): all-IP, OFDMA-based radio with tens to hundreds of Mbps, "
     "making HD streaming, VoIP and app-driven services practical."),
    ("5G", "low latency, massive IoT and multi-Gbps (eMBB/URLLC/mMTC)",
     ["5g", "low latency", "ultra reliable", "urllc", "embb", "mmtc", "massive iot", "iot",
      "internet of things", "sensor*", "million devices", "smart factory", "industrial automation",
      "robot*", "remote surgery", "telesurgery", "autonomous", "self driving", "v2x", "network slicing",
      "private network", "mmwave", "millimeter wave", "augmented reality", "virtual reality", "vr",
      "real time control", "1 ms", "smart city", "smart grid"],
     "5G (NR; IMT-2020): ~1 ms URLLC latency, 1 million devices/km2 (mMTC) and 20 Gbps peak / "
     "100 Mbps user-experienced eMBB targets."),
    ("6G", "AI-native networks, sensing and immersive communication (IMT-2030)",
     ["6g", "holographic", "hologram*", "digital twin*", "terahertz", "thz", "integrated sensing",
      "sensing and communication", "joint communication and sensing", "ai native", "native ai",
      "ai and communication", "tbps", "terabit", "immersive communication", "ubiquitous connectivity",
      "non terrestrial"],
     "6G (IMT-2030; framework M.2160, requirements in draft): six usage scenarios incl. integrated "
     "sensing, AI-and-communication and immersive communication."),
]

NO_MATCH = "No clear match"


def norm(text):
    """Lowercase, turn hyphens/slashes/underscores into spaces, collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[-_/]", " ", text.lower())).strip()


def hit(text, kw):
    kw = norm(kw)
    pat = r"\b" + re.escape(kw[:-1]) if kw.endswith("*") else r"\b" + re.escape(kw) + r"\b"
    return re.search(pat, text) is not None


def recommend(description):
    """Return a dict describing the recommendation for one description."""
    text = norm(description)
    scored = []                                         # (rule index, generation, hits)
    for idx, (gen, _cls, kws, _why) in enumerate(RULES):
        hits = [k for k in kws if hit(text, k)]
        if hits:
            scored.append((idx, gen, hits))
    if not scored:
        return {"gen": NO_MATCH, "hits": [], "tied": [], "also": [],
                "why": "No keyword matched. The need may be generation-independent (e.g. coverage, "
                       "battery life, price) or phrased with words the tool does not know."}
    top = max(len(h) for _, _, h in scored)
    tied = [s for s in scored if len(h := s[2]) == top]
    winner = min(tied, key=lambda s: s[0])              # earliest generation among the best
    idx, gen, hits = winner
    return {"gen": gen, "hits": hits, "tied": [t[1] for t in tied] if len(tied) > 1 else [],
            "also": [(g, len(h)) for i, g, h in scored if g != gen and g not in [t[1] for t in tied]],
            "why": RULES[idx][3]}


def format_result(res):
    lines = [f"Result : {res['gen']}", f"Why    : {res['why']}"]
    if res["hits"]:
        lines.append(f"Matched: {', '.join(res['hits'])}")
    if res["tied"]:
        lines.append(f"Note   : AMBIGUOUS - tied between {', '.join(res['tied'])}; earliest returned "
                     f"because the question asks which generation came first.")
    elif res["also"]:
        lines.append("Note   : also partly matches " + ", ".join(f"{g} ({n})" for g, n in res["also"]))
    return "\n".join(lines)


# (description, acceptable results). Written BEFORE running; see Research Notes Part C.
ROUND1 = [
    ("Make a phone call while walking down the street", ["1G"]),
    ("Stop strangers listening in on my calls and let me send a quick text to a friend", ["2G"]),
    ("Check my email on my phone and pay only for the data I use, not the minutes", ["2.5G"]),
    ("Video chat with my grandmother and browse the web on a handheld device", ["3G"]),
    ("Stream a high-definition movie on a train", ["4G"]),
    ("Remotely operate a surgical robot with almost no delay", ["5G"]),
    ("Let a hundred thousand parking sensors report once an hour across a city", ["5G"]),
    ("Walk into a virtual meeting room and interact with a hologram of a colleague", ["6G"]),
    ("Reach someone using a vehicle radio and an operator who connects the call by hand", ["0G"]),
    ("Improve coverage and battery life in a remote village", [NO_MATCH]),          # does not map cleanly
    ("Use the same number abroad and keep my calls private", ["2G"]),
    ("Send a photo message and watch a short video clip on my phone", ["2.5G", "3G"]),  # spans two
]

# Round 2: new sentences, written before running, after the one vocabulary fix above
ROUND2 = [
    ("Travel overseas and keep using my phone without changing the SIM", ["2G"]),
    ("Browse the news on my phone while commuting", ["3G"]),
    ("Control a fleet of warehouse robots with split-second reactions", ["5G"]),
    ("Share a mobile hotspot with my laptop for a video conference", ["4G"]),
    ("Send a picture message to my brother over a packet data network", ["2.5G"]),
    ("Detect moving objects using the same radio signals that carry my data", ["6G"]),
    ("Lower my monthly phone bill", [NO_MATCH]),                                    # out of scope
    ("Play online games with friends and read data from temperature sensors", ["4G", "5G"]),  # spans two
]

if __name__ == "__main__":
    if "-i" in sys.argv:
        print("Describe a communication requirement (blank line to quit).")
        while True:
            try:
                s = input("> ").strip()
            except EOFError:
                break
            if not s:
                break
            print(format_result(recommend(s)), "\n")
    else:
        for title, tests in (("ROUND 1 (re-run with the fixed keyword list)", ROUND1), ("ROUND 2 (new sentences)", ROUND2)):
            ok = 0
            print("=" * 18, title, "=" * 18)
            for i, (desc, expected) in enumerate(tests, 1):
                res = recommend(desc)
                good = res["gen"] in expected
                ok += good
                print(f"{i}. Input   : {desc}\n   Expected: {' or '.join(expected)}   ->   "
                      f"{'PASS' if good else 'MISS'}")
                print("   " + format_result(res).replace("\n", "\n   ") + "\n")
            print(f"{title}: {ok}/{len(tests)} as expected\n")