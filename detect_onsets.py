import numpy as np
import librosa
import math
from matplotlib import pyplot as plt


def get_beats(audio_file):
    # 加载音频文件并获取音频信号（y）和采样率（sr）
    y, sr = librosa.load(audio_file)
    # 计算音频信号的起始强度
    onset_env = librosa.beat.onset.onset_strength(y=y, sr=sr)
    # 从起始强度中计算 PLP（脉冲）信号
    # pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr, hop_length=512)
    pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr, hop_length=315)
    # 查找音频中的拍速和拍点位置
    # tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env)
    # 查找 PLP 信号中的局部最大值以识别 PLP 拍点
    beats_plp = np.flatnonzero(librosa.util.localmax(pulse))
    # 创建一个 Matplotlib 图形，包含两个子图
    fig, ax = plt.subplots(nrows=2, sharex=True, sharey=False)
    # 在第一个子图中绘制起始强度和检测到的拍点
    times = librosa.times_like(onset_env, sr=sr)
    ax[0].plot(times, librosa.util.normalize(onset_env), label='Onset Strength')
    # ax[0].vlines(times[beats], 0, 1, alpha=0.5, color='r', linestyle='--', label='Beats')
    ax[0].legend()
    ax[0].set(title='librosa.beat.beat_track')
    ax[0].label_outer()

    times = librosa.times_like(pulse, sr=sr)
    ax[1].plot(times, librosa.util.normalize(pulse), label='PLP')
    print(times[beats_plp])
    ax[1].vlines(times[beats_plp], 0, 1, alpha=0.5, color='r', linestyle='--', label='PLP Beats')
    ax[1].legend()
    ax[1].set(title='librosa.beat.plp', xlim=[25, 35])
    ax[1].set(title='librosa.beat.plp')
    ax[1].xaxis.set_major_formatter(librosa.display.TimeFormatter())
    # 显示 Matplotlib 绘图
    plt.show()

    return times[beats_plp]


def get_timeline_from_beat_times(beat_times: np.ndarray):
    max_time = math.floor(beat_times[-1])
    timeline1 = np.zeros(max_time + 1)
    timeline2 = np.zeros(max_time + 1)
    # each item in timeline dedicates the ppm of the corresponding second

    # method 1:
    for i in range(len(beat_times) - 1):
        start = math.floor(beat_times[i])
        end = math.floor(beat_times[i + 1])
        timeline1[start:end] = 60 / (beat_times[i + 1] - beat_times[i])

    # method 2:
    # 构建dict储存每秒内的beats时间
    beat_dict = {}
    for i in range(len(beat_times)):
        second = math.floor(beat_times[i])
        if second not in beat_dict:
            beat_dict[second] = [beat_times[i]]
        else:
            beat_dict[second].append(beat_times[i])

    # 从相邻两秒计算ppm
    for i in range(max_time + 1):
        if i - 1 in beat_dict and i in beat_dict:
            timeline2[i] = 60 * (len(beat_dict[i]) + len(beat_dict[i-1]) - 1) / (beat_dict[i][-1] - beat_dict[i-1][0])
        elif i in beat_dict and i + 1 in beat_dict:
            timeline2[i] = 60 * (len(beat_dict[i]) + len(beat_dict[i+1]) - 1) / (beat_dict[i+1][-1] - beat_dict[i][0])
        elif i in beat_dict and len(beat_dict[i]) > 1:
            timeline2[i] = 60 / (beat_dict[i][-1] - beat_dict[i][0])
        else:
            timeline2[i] = 0
            if i - 1 in beat_dict:
                timeline2[i] = timeline2[i-1]

    # 计算为整数
    timeline2 = np.int32(np.round(timeline2))

    # 自定义转换
    lst = timeline2.tolist()
    for i, item in enumerate(lst):
        if item > 220:
            lst[i] = 220
        if i > 0 and abs(lst[i] - lst[i - 1]) > 20:
            lst[i] = lst[i - 1]

    # 绘制timeline和timeline2的对比图,加上图例
    plt.plot(timeline1, label='timeline1')
    plt.plot(timeline2, label='timeline2')
    plt.plot(lst, label='lst')
    plt.ylim(0, 220)
    plt.legend()
    plt.show()

    # print(beat_dict[max_time], beat_dict[max_time-1], beat_dict[max_time-2])

    return timeline2


# 示例用法
audio_file = "H:\\视频\\LM\\240731_play\\press2\\240730_press2_ECG_1.wav"
print(f"[Process] Fetching audio {audio_file}")
beats = get_beats(audio_file)
print("[Process] Calculating PPM")
timeline = get_timeline_from_beat_times(beats)
# timeline取整

print("Timeline: ", timeline)

lst = timeline.tolist()
for i, item in enumerate(lst):
    if item > 220:
        lst[i] = 220
    if i > 0 and abs(lst[i] - lst[i-1]) > 50:
        lst[i] = lst[i-1]

# 写到txt文件
with open('timeline.txt', 'w') as f:
    f.write(str(lst))
