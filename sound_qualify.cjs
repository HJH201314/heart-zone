const { exec, spawnSync } = require('child_process');
const path = require('path');

// 设置输入和输出文件路径
const inputFilePath = path.join(__dirname, 'input/sample.wav');

// 采样率转换、带通滤波
const fixAudio = (inputFile, sampleRate = 44100, bandpass = false, bandpassFreq = 50, width = 150) => new Promise((resolve, reject) => {
  // 拼接输出文件名 inputFileName_bandpass.wav
  const outputFile = inputFile.replace('.wav', '_bandpass.wav').replace('input', 'output');

  // 构造ffmpeg命令
  const bandpassFilter = bandpass ? `bandpass=f=${bandpassFreq}:width_type=h:width=${width}` : 'anull'; // 带通滤波器或空滤波器
  const ffmpegCommand = `ffmpeg -hide_banner -i "${inputFile}" -ar ${sampleRate} -af "${bandpassFilter}" "${outputFile}" -y`;

  // 执行ffmpeg命令
  exec(ffmpegCommand, (error, stdout, stderr) => {
    if (error) {
      console.error(`[preprocess] 执行错误: ${error.message}`);
      return reject(error.message);
    }
    console.log(`[preprocess] 预处理完成，文件: ${outputFile}`);
    return resolve(outputFile);
  });
});

// 音频标准化
const normalizeAudio = (inputFile) => new Promise((resolve, reject) => {
  const outputFile = inputFile.replace('.wav', '_normalized.wav').replace('input', 'output');

  // 计算音频信息
  const { stderr } = spawnSync('ffmpeg', ['-hide_banner', '-i', inputFile, '-af', 'loudnorm=I=-14:TP=-2:LRA=10:print_format=json', '-f', 'null', '-'], { encoding: 'utf8' });
  const audioInfos = parseJsonFromStderr(stderr);
  if (audioInfos) {
    console.log(`[normalize_1] 音频信息: ${JSON.stringify(audioInfos[0])}`);
  }
  // 标准化音频
  const { input_i, input_tp, input_lra, target_offset, input_thresh } = audioInfos[0];
  const loudnorm = `loudnorm=I=-14:TP=-2:LRA=10:measured_I=${input_i}:measured_TP=${input_tp}:measured_LRA=${input_lra}:measured_thresh=${input_thresh}:offset=${target_offset}:linear=true:print_format=summary`;
  const ffmpegCommand = `ffmpeg -hide_banner -i "${inputFile}" -af "${loudnorm}" "${outputFile}" -y`;
  exec(ffmpegCommand, {
    cwd: __dirname
  }, (error, stdout, stderr) => {
    if (error) {
      console.error(`[normalize_2] 执行错误: ${error.message}`);
      reject(error.message);
    }
    console.log(`[normalize_2] 标准化完成: ${outputFile}`);
    resolve(outputFile);
  });
});

// 从stderr中解析JSON数据
function parseJsonFromStderr(stderr) {
  // 假设stderr中包含JSON数据
  try {
    const jsonPattern = /\{[^]*?\}/g; // 匹配可能的JSON对象
    const matches = stderr.match(jsonPattern);
    if (matches) {
      return matches.map(match => JSON.parse(match)); // 解析JSON字符串
    }
  } catch (error) {
    console.error('解析JSON时出错:', error.message);
  }
  return null;
}

async function main() {
  // 调用音频处理函数，先标准化再变频，可以避免底噪
  const output = await normalizeAudio(inputFilePath);
  await fixAudio(output);
}

main();