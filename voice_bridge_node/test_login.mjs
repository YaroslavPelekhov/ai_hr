import 'dotenv/config'
import { Client, GatewayIntentBits } from 'discord.js'

console.log('Node', process.version, '| starting test...')
const client = new Client({ intents: [GatewayIntentBits.Guilds] })

client.on('debug', m => console.log('[debug]', m))
client.on('warn', m => console.warn('[warn]', m))
client.on('error', e => console.error('[error]', e))
client.on('shardError', e => console.error('[shardError]', e))
client.on('shardDisconnect', (e, id) => console.error('[shardDisconnect]', id, e?.code))
client.on('invalidated', () => console.error('[invalidated]'))
client.once('ready', () => console.log('READY as', client.user?.tag))

const token = process.env.DISCORD_BOT_TOKEN
console.log('Have token?', Boolean(token))

console.log('Logging in...')
try {
  await client.login(token)
  console.log('login() resolved')
} catch (e) {
  console.error('login() rejected:', e)
}
setTimeout(() => console.log('Still alive after 10s'), 10_000)
