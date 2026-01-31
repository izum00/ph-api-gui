import fetch from "node-fetch";
import ffmpeg from "fluent-ffmpeg";
import { PassThrough } from "stream";
import fs from "fs";
import { tmpdir } from "os";
import { join } from "path";
import { promisify } from "util";
import ffmpegPath from "ffmpeg-static";
ffmpeg.setFfmpegPath(ffmpegPath);

const writeFile = promisify(fs.writeFile);
const unlink = promisify(fs.unlink);

export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const { urls } = req.body;
    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({ error: "No m3u8 URLs provided" });
    }

    // 一時ファイルとして結合用のTSファイルを作る
    const tempFiles = [];

    for (let i = 0; i < urls.length; i++) {
      const url = urls[i];
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Failed to fetch ${url}`);
      const data = await response.arrayBuffer();
      const tempPath = join(tmpdir(), `segment-${i}.ts`);
      await writeFile(tempPath, Buffer.from(data));
      tempFiles.push(tempPath);
    }

    // 結合した出力ファイル
    const outputPath = join(tmpdir(), `output.mp4`);

    // ffmpegで結合
    await new Promise((resolve, reject) => {
      const command = ffmpeg();

      tempFiles.forEach((file) => command.input(file));

      command
        .on("error", (err) => reject(err))
        .on("end", () => resolve())
        .mergeToFile(outputPath, tmpdir());
    });

    // 結果をData URLとして返す
    const videoBuffer = fs.readFileSync(outputPath);
    const base64 = videoBuffer.toString("base64");
    const dataUrl = `data:video/mp4;base64,${base64}`;

    // 一時ファイル削除
    await Promise.all([...tempFiles, outputPath].map((file) => unlink(file)));

    res.status(200).json({ dataUrl });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
}
