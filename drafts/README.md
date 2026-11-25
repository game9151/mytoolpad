# Drafts

Not deployed (see .vercelignore).

## Car diagnostics simulator

It is live: `car-diagnostics-simulator.html` in the site root, pictures in `assets/car-sim/`.
Run `python3 build.py` after changing either, so the cache version updates.

Test locally from the site root:

    python3 -m http.server 8766

then open http://localhost:8766/car-diagnostics-simulator.html

`car-sim/blender/` holds the 3D source. Re-render (about 15 minutes, writes into assets/car-sim):

    /Applications/Blender.app/Contents/MacOS/Blender -b -P drafts/car-sim/blender/build_bay.py -- assets/car-sim 100 80 CPU

Use CPU. GPU (Metal) rendering hangs on this Mac.

## car-diagnostics-simulator.html (this folder)

The first version. Kept for reference only.
