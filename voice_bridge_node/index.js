// index.js — Discord ↔ локальный API мост (ESM, Node 18+)
import 'dotenv/config';
import { Client, GatewayIntentBits, Partials } from 'discord.js';
import {
  joinVoiceChannel,
  EndBehaviorType,
  createAudioPlayer,
  createAudioResource,
  VoiceConnectionStatus,
  entersState,
  AudioPlayerStatus,
} from '@discordjs/voice';
import prism from 'prism-media';
import { WaveFile } from 'wav';
import { Readable } from 'node:stream';

// ===== ENV =====
const TOKEN = process.env.DISCORD_BOT_TOKEN;
const PY_API_BASE = process.env.PY_API_BASE || 'http://127.0.0.1:8000';
const MODEL = process.env.MODEL || '4o-mini';
const BUDGET_USD = parseFloat(process.env.BUDGET_USD || '0.90');
const MINUTES_IN = parseInt(process.env.MINUTES_LIMIT_IN || '60', 10);
const MINUTES_OUT = parseInt(process.env.MINUTES_LIMIT_OUT || '30', 10);
const LIMIT_MODE = process.env.LIMIT_MODE || 'soft';

if (!TOKEN) {
  console.error('❌ Missing DISCORD_BOT_TOKEN in .env');
  process.exit(1);
}

// ===== helpers =====
function pcmToWav(pcmBuffer, { sampleRate = 48000, channels = 2, bitDepth = 16 } = {}) {
  const wf = new WaveFile();
  wf.fromScratch(channels, sampleRate, bitDepth.toString(), pcmBuffer);
  return Buffer.from(wf.toBuffer());
}

function makeFormDataForStt(wavBuffer, filename = 'chunk.wav') {
  const form = new FormData();
  const blob = new Blob([wavBuffer], { type: 'audio/wav' });
  form.append('file', blob, filename);
  return form;
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ===== discord client =====
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
  partials: [Partials.Channel],
});

client.once('ready', () => {
  console.log(`Logged in as ${client.user.tag}`);
  console.log(`[Limiter] MODEL=${MODEL} | BUDGET_USD=${BUDGET_USD} | MIN_IN=${MINUTES_IN} | MIN_OUT=${MINUTES_OUT} | MODE=${LIMIT_MODE}`);
});

// один плеер на голосовой канал
const players = new Map(); // voiceChannelId -> audioPlayer

// ===== commands =====
client.on('messageCreate', async (msg) => {
  try {
    if (!msg.guild || msg.author.bot) return;
    const content = (msg.content || '').trim();

    if (content.startsWith('!join')) {
      const member = await msg.guild.members.fetch(msg.author.id);
      const voice = member?.voice?.channel;
      if (!voice) return msg.reply('Зайдите в голосовой канал и повторите `!join`');
      await joinAndRecord(voice, msg.channel);
      return msg.reply(`Подключился к **${voice.name}**. Говорите — транскрибирую. Напишите \`!finish\` чтобы завершить.`);
    }

    if (content.startsWith('!status')) {
      return msg.reply(
        [
          `MODEL: ${MODEL}`,
          `Budget: $${BUDGET_USD.toFixed(2)}`,
          `Minutes IN: ${MINUTES_IN}, OUT: ${MINUTES_OUT}`,
          `Mode: ${LIMIT_MODE}`,
          `API: ${PY_API_BASE}`,
        ].join('\n')
      );
    }

    if (content.startsWith('!finish')) {
      try {
        const form = new FormData();
        form.append('channel_id', msg.channel.id);
        form.append('candidate_id', '');
        const res = await fetch(`${PY_API_BASE}/finish`, { method: 'POST', body: form });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const parts = [];
        if (data?.decision) parts.push(`Решение: **${data.decision}**`);
        if (data?.report) parts.push(`Отчёт: ${data.report}`);
        if (!parts.length) parts.push('Завершил. (нет данных решения)');
        return msg.reply(parts.join('\n'));
      } catch (e) {
        console.warn('finish error:', e);
        return msg.reply('Завершил. (не удалось получить решение)');
      }
    }
  } catch (e) {
    console.error('messageCreate error:', e);
  }
});

// ===== voice =====
async function joinAndRecord(voiceChannel, textChannel) {
  const connection = joinVoiceChannel({
    channelId: voiceChannel.id,
    guildId: voiceChannel.guild.id,
    adapterCreator: voiceChannel.guild.voiceAdapterCreator,
    selfDeaf: false,
    selfMute: false,
  });

  try {
    await entersState(connection, VoiceConnectionStatus.Ready, 15_000);
    console.log('Voice ready.');
  } catch {
    console.error('Voice connection failed to become ready in time.');
  }

  const receiver = connection.receiver;

  receiver.speaking.on('start', (userId) => {
    try {
      const opusStream = receiver.subscribe(userId, {
        end: { behavior: EndBehaviorType.AfterSilence, duration: 1200 },
      });

      const pcmDecoder = new prism.opus.Decoder({ rate: 48000, channels: 2, frameSize: 960 });
      const chunks = [];
      opusStream.pipe(pcmDecoder);

      pcmDecoder.on('data', (buf) => chunks.push(buf));

      pcmDecoder.on('end', async () => {
        if (!chunks.length) return;

        const pcmBuffer = Buffer.concat(chunks);
        const wavBuffer = pcmToWav(pcmBuffer, { sampleRate: 48000, channels: 2 });

        try {
          const form = makeFormDataForStt(wavBuffer, 'chunk.wav');
          form.append('channel_id', textChannel.id);
          form.append('user_id', userId);

          const res = await fetch(`${PY_API_BASE}/stt`, { method: 'POST', body: form });
          if (!res.ok) throw new Error(`STT HTTP ${res.status}`);
          const data = await res.json();

          if (data?.text) {
            await textChannel.send(`🗣️ <@${userId}>: ${data.text}`);
          }

          if (data?.next_question) {
            await textChannel.send(`🤖 Вопрос: ${data.next_question}`);
            try {
              const ttsRes = await fetch(`${PY_API_BASE}/tts?text=${encodeURIComponent(data.next_question)}`);
              if (!ttsRes.ok) throw new Error(`TTS HTTP ${ttsRes.status}`);
              const nodeStream = Readable.fromWeb(ttsRes.body);
              const resource = createAudioResource(nodeStream);

              let player = players.get(voiceChannel.id);
              if (!player) {
                player = createAudioPlayer();
                players.set(voiceChannel.id, player);
                connection.subscribe(player);
              }
              player.play(resource);
            } catch (e) {
              console.warn('TTS play failed:', e.message || e);
            }
          }
        } catch (e) {
          console.warn('STT error:', e.message || e);
        }
      });
    } catch (e) {
      console.error('receiver.speaking handler error:', e);
    }
  });
}

// ===== start =====
client.login(TOKEN).catch((e) => {
  console.error('Login failed:', e);
  process.exit(1);
});
