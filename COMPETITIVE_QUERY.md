# Native bot query reporting

Based on ReHLDS tag 3.15.0.896 (1963001).

When the game DLL registers `bot_enable_query_hook` and its value is positive,
Steam bot metadata reports zero bots, matching the native ReGameDLL query hook.
Missing, zero or negative values retain normal engine bot counts. Updates occur
through the existing server-details refresh, approximately once per second.
The engine does not register or persist a second copy of the game DLL cvar.

Only published bot metadata changes. Server totals, fakeclient flags, bot AI,
authentication and gameplay are unchanged. This does not establish that external
monitoring cannot identify bots through other data or heuristics.

Build on Linux with `cmake -S . -B build-competitive -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_CXX_FLAGS=-fPIC -DCMAKE_C_FLAGS=-fPIC -DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,notext -DUSE_STATIC_LIBSTDC=OFF`
and `cmake --build build-competitive --target engine -j 4`.
Install only the resulting `build-competitive/rehlds/engine_i486.so` into a stopped
dedicated ReHLDS server, keeping its existing compatible Steam library. Never
replace Steam client game engine libraries with this dedicated-server engine.

Run `python3 tools/test_steam_reporting.py` for the real-method forwarding test.

When the game DLL enables `bot_show_latency`, the engine omits fake clients from
its ordinary scoreboard ping packets. The native bot DLL already sends their
display latency periodically; overwriting those values with engine zeroes caused
visible flickering while the standard scoreboard was open. Human ping/loss and
the normal bot entries when the feature is disabled retain their existing behavior.
Run `python3 tools/test_scoreboard_pings.py` to check the actual emitter with a
recording packet writer, including repeated updates and disabled-mode fallback.
