#!/usr/bin/env python3
"""Compile the real server-details method against a recording Steam interface."""
from pathlib import Path
import subprocess, tempfile
root=Path(__file__).resolve().parents[1]
s=(root/'rehlds/engine/sv_steam3.cpp').read_text()
a=s.index('void CSteam3Server::SendUpdatedServerDetails()')
b=s.index('\nvoid CSteam3Client::Shutdown()',a)
method=s[a:b]
fixture=r'''#include <cassert>
#include <cstring>
struct Client {bool active=false,spawned=false,connected=false,fakeclient=false;};
struct {int maxclients=0;Client clients[32];} g_psvs;
struct {const char *name="de_dust2";} g_psv;
struct {float value=-1;} sv_visiblemaxplayers;
enum {ca_dedicated=1};struct {int state=ca_dedicated;} g_pcls;
float query=0;bool registered=false;
float Cvar_VariableValue(const char *name){assert(!strcmp(name,"bot_enable_query_hook"));return registered?query:0;}
const char *Cvar_VariableString(const char*){return "fixture";}
struct Steam {int bots=-1,max=-1;void SetBotPlayerCount(int n){bots=n;}void SetMaxPlayerCount(int n){max=n;}
void SetServerName(const char*){}void SetMapName(const char*){};} steam;
struct CRehldsPlatformHolder {static CRehldsPlatformHolder* get(){static CRehldsPlatformHolder p;return &p;}Steam *SteamGameServer(){return &steam;}};
struct CSteam3Server {void SendUpdatedServerDetails();void UpdateGameTags(){}};
'''
fixture+=method
fixture+=r'''
int main(){
 CSteam3Server server;g_psvs.maxclients=5;
 g_psvs.clients[0].active=true;g_psvs.clients[0].fakeclient=true;
 g_psvs.clients[1].spawned=true;g_psvs.clients[1].fakeclient=true;
 g_psvs.clients[2].connected=true; // real human
 g_psvs.clients[3].fakeclient=true; // disconnected bot must not count
 server.SendUpdatedServerDetails();assert(steam.bots==2 && steam.max==5);
 registered=true;query=1;server.SendUpdatedServerDetails();assert(steam.bots==0 && steam.max==5);
 g_pcls.state=0;server.SendUpdatedServerDetails();assert(steam.bots==2);
 g_pcls.state=ca_dedicated;query=0;server.SendUpdatedServerDetails();assert(steam.bots==2);
 query=-1;server.SendUpdatedServerDetails();assert(steam.bots==2);
 query=1;registered=false;server.SendUpdatedServerDetails();assert(steam.bots==2);
 registered=true;query=1;g_psvs.maxclients=0;server.SendUpdatedServerDetails();assert(steam.bots==0);
}
'''
with tempfile.TemporaryDirectory(prefix='rehlds-steam-test-') as directory:
 p=Path(directory);(p/'fixture.cpp').write_text(fixture)
 subprocess.run(['g++','-std=c++14',str(p/'fixture.cpp'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS: Steam reporting on/off/missing/unloaded cvar, occupied bot filtering, unchanged capacity')
