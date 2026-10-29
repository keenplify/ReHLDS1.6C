#!/usr/bin/env python3
"""Exercise the actual ping emitter with recording message writers."""
from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
source = (root / 'rehlds/engine/sv_main.cpp').read_text()
start = source.index('void EXT_FUNC SV_EmitPings_internal(')
end = source.index('\nvoid SV_WriteEntitiesToClient(', start)
method = source[start:end]
fixture = r'''
#include <cassert>
#include <cstring>
#include <vector>
#define EXT_FUNC
struct client_t { bool active=false, fakeclient=false; int ping=0, loss=0; };
struct sizebuf_t {};
struct { int maxclients=4; client_t clients[4]; } g_psvs;
float latency=0;
float Cvar_VariableValue(const char *name) { assert(!strcmp(name,"bot_show_latency")); return latency; }
constexpr int svc_pings=17;
std::vector<unsigned> writes;
void MSG_WriteByte(sizebuf_t *, int value) { assert(value==svc_pings); }
void MSG_StartBitWriting(sizebuf_t *) {}
void MSG_EndBitWriting(sizebuf_t *) {}
void MSG_WriteBits(unsigned value, int) { writes.push_back(value); }
void SV_GetNetInfo(client_t *client, int *ping, int *loss) { *ping=client->ping; *loss=client->loss; }
'''
fixture += method
fixture += r'''
int main() {
 sizebuf_t msg;
 g_psvs.clients[0]={true,false,72,3};
 g_psvs.clients[1]={true,true,0,0};
 g_psvs.clients[2]={false,true,0,0};
 g_psvs.clients[3]={true,false,41,0};
 auto emit=[&](){writes.clear();SV_EmitPings_internal(nullptr,&msg);};
 latency=1;emit();
 assert((writes==std::vector<unsigned>{1,0,72,3,1,3,41,0,0}));
 for(int i=0;i<50;++i) {emit();assert(writes.size()==9);}
 for(float disabled: {0.0f,-1.0f}) {
  latency=disabled;emit();
  assert((writes==std::vector<unsigned>{1,0,72,3,1,1,0,0,1,3,41,0,0}));
 }
 latency=1;g_psvs.maxclients=0;emit();assert((writes==std::vector<unsigned>{0}));
}
'''
with tempfile.TemporaryDirectory(prefix='rehlds-pings-') as directory:
    path=Path(directory)
    (path/'fixture.cpp').write_text(fixture)
    subprocess.run(['g++','-std=c++14',str(path/'fixture.cpp'),'-o',str(path/'test')],check=True)
    subprocess.run([str(path/'test')],check=True)
print('PASS: native bot latency has one writer; human latency/loss and disabled-mode bot reporting are preserved')
