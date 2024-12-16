import { exec } from "child_process";
import cors from "cors";
import dotenv from "dotenv";
import voice from "elevenlabs-node";
import express from "express";
import { promises as fs } from "fs";
import { spawn } from 'child_process';
import OpenAI from "openai";

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || "-", // Your OpenAI API key here, I used "-" to avoid errors when the key is not set but you should not do that
});

const elevenLabsApiKey = process.env.ELEVEN_LABS_API_KEY;
const voiceID = "ZJCNdZEjYwkOElxugmW2";

const app = express();
app.use(express.json());
app.use(cors());
const port = 3000;

function decodeUnicode(str) {
  return str.replace(/\\u[\dA-F]{4}/gi, (match) => {
    return String.fromCharCode(parseInt(match.replace(/\\u/, ''), 16));
  });
}

app.get("/", (req, res) => {
  res.send("Hello World!");
});

app.get("/voices", async (req, res) => {
  res.send(await voice.getVoices(elevenLabsApiKey));
});

const execCommand = (command) => {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) reject(error);
      resolve(stdout);
    });
  });
};

const lipSyncMessage = async (message) => {
  const time = new Date().getTime();
  console.log(`Starting conversion for message ${message}`);
  await execCommand(
    `${process.env.FFMPEG_PATH} -y -i audios/message_${message}.mp3 audios/message_${message}.wav`
    // -y to overwrite the file
  );
  console.log(`Conversion done in ${new Date().getTime() - time}ms`);
  await execCommand(
    `bin\\rhubarb -f json -o audios/message_${message}.json audios/message_${message}.wav -r phonetic`
  );
  // -r phonetic is faster but less accurate
  console.log(`Lip sync done in ${new Date().getTime() - time}ms`);
};



app.post("/chat", async (req, res) => {
  console.log(`${process.env.PYTHON_PATH}`)
  const userMessage = req.body.message;
  if (!userMessage) {
    res.send({
      messages: [
        {
          text: "Hey dear... How was your day?",
          audio: await audioFileToBase64("audios/intro_0.wav"),
          lipsync: await readJsonTranscript("audios/intro_0.json"),
          facialExpression: "smile",
          animation: "Talking_1",
        },
        {
          text: "I missed you so much... Please don't go for so long!",
          audio: await audioFileToBase64("audios/intro_1.wav"),
          lipsync: await readJsonTranscript("audios/intro_1.json"),
          facialExpression: "sad",
          animation: "Crying",
        },
      ],
    });
    return;
  }
  if (!elevenLabsApiKey || openai.apiKey === "-") {
    res.send({
      messages: [
        {
          text: "Please my dear, don't forget to add your API keys!",
          audio: await audioFileToBase64("audios/api_0.wav"),
          lipsync: await readJsonTranscript("audios/api_0.json"),
          facialExpression: "angry",
          animation: "Angry",
        },
        {
          text: "You don't want to ruin Wawa Sensei with a crazy ChatGPT and ElevenLabs bill, right?",
          audio: await audioFileToBase64("audios/api_1.wav"),
          lipsync: await readJsonTranscript("audios/api_1.json"),
          facialExpression: "smile",
          animation: "Laughing",
        },
      ],
    });
    return;
  }
  const python = spawn(`${process.env.PYTHON_PATH || 'python'}`, ['query.py', userMessage]);

  let result = '';
  python.stdout.on('data', (data) => {
    result += decodeUnicode(data.toString());
  });

  python.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
  });

  python.on('close', async (code) => {
    if (code === 0) {
      result = JSON.stringify(result);
      result = result.slice(1, -1);
      result = result.replace(/\\r\\n/g, "")  // \r\n 제거
      .replace(/\\/g, "");     // \ 제거

      result = '{"messages" : ' + result + '}';
      console.log(result);
      const responseData = JSON.parse(result);
      let messages = responseData.messages;
      if (!messages){
        messages = [];
      }
      if (messages.messages) {
        messages = messages.messages; // ChatGPT가 메시지를 바로 반환하거나 messages 속성으로 반환하는 경우 처리
      }

      // 각 메시지에 대해 음성 생성과 립싱크 처리
      for (let i = 0; i < messages.length; i++) {
        const message = messages[i];
        const fileName = `audios/message_${i}.mp3`; // 음성 파일 이름
        const textInput = message.text; // 텍스트 입력
        console.log(textInput);

        // 음성 파일 생성
        await voice.textToSpeech(elevenLabsApiKey, voiceID, fileName, textInput);

        // 립싱크 처리
        await lipSyncMessage(i);

        message.audio = await audioFileToBase64(fileName);
        message.lipsync = await readJsonTranscript(`audios/message_${i}.json`);
      }

      // 모든 처리 완료 후 응답 전송
      res.send({ messages });
    } else {
      res.status(500).json({ error: 'Python script error' });
    }
  });
});

const readJsonTranscript = async (file) => {
  const data = await fs.readFile(file, "utf8");
  return JSON.parse(data);
};

const audioFileToBase64 = async (file) => {
  const data = await fs.readFile(file);
  return data.toString("base64");
};

app.listen(port, () => {
  console.log(`자립준비청년 대상 버추얼 도우미 listening on port ${port}`);
});
