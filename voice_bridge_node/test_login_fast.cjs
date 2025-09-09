require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');

console.log('Node', process.version, '| fast login test…');
const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.on('debug', m => console.log('[debug]', m));
client.on('warn',  m => console.warn('[warn]', m));
client.on('error', e => console.error('[error]', e));

let done = false;
const quit = (code=0)=>{ if(!done){ done=true; process.exit(code); } };

client.once('ready', () => { 
  console.log('READY as', client.user?.tag); 
  quit(0);
});

const token = process.env.DISCORD_BOT_TOKEN;
if (!token) { console.error('No DISCORD_BOT_TOKEN in .env'); quit(1); }

console.log('Logging in…');
client.login(token).catch(e => { console.error('login() rejected:', e); quit(1); });

// fail-fast через 5 секунд, если READY не пришёл
setTimeout(()=>{ console.error('Timeout: no READY within 5s'); quit(1); }, 5000);
