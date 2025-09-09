require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');

console.log('Node', process.version, '| starting test...');
const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.on('debug', m => console.log('[debug]', m));
client.on('warn', m => console.warn('[warn]', m));
client.on('error', e => console.error('[error]', e));
client.on('shardError', e => console.error('[shardError]', e));
client.on('shardDisconnect', (e, id) => console.error('[shardDisconnect]', id, e?.code));

client.once('ready', () => console.log('READY as', client.user?.tag));
client.once('clientReady', () => console.log('clientReady event fired'));

const token = process.env.DISCORD_BOT_TOKEN;
console.log('Have token?', Boolean(token), 'len:', (token||'').length);

console.log('Logging in...');
client.login(token).then(
  () => console.log('login() resolved'),
  (e) => console.error('login() rejected:', e)
);
setTimeout(()=>console.log('Still alive after 15s'),15000);
