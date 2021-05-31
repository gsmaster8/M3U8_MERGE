# M3U8_MERGE

## 依赖
	python3

-   Centos
-   sudo yum install python3
-
-   Ubuntu
-   sudo apt-get install python3

### python3 依赖包
-	sortedcontainers
-	pip3 install sortedcontainers

## M3U8_MERGE工具使用方法

-   单流录制模式下，每个uid的音频数据和视频数据分开存储，音视频合并转码脚本可以合并每个 uid 的音频文件和视频文件。
    
### 使用方法： 
    1、运行合并脚本：python3 TRTC_Merge.py [option] 
    2、会在录制文件目录下生成合并后的mp4文件。
> 如：python3 TRTC_Merge.py -f /xxx/file -m 0 
     
-   [option]的可选参数和对应功能见下表。

|参数| 功能 |
|--|--|
|-f | 指定待合并文件的存储路径。如果有多个uid的录制文件，脚本均会对其进行转码。 |
|-m   | 0：分段模式(默认设置)。此模式下，脚本将每个uid下的录制文件按Segment合并。 <br>1：合并模式。一个uid下的所有音视频文件转换为一个文件。|
|-s|保存模式。如果设置了该参数，则合并模式下的Segment之间的空白部分被删除，文件的实际时常小于物理时常。|
|-a|0: 禁用辅流(默认设置)。1: 替代模式，若主流不存在，则使用辅流。2: 禁用主流|
|-p|指定输出视频的fps。默认为15 fps，有效范围5-120 fps，低于5 fps计为5 fps，高于120 fps计为120 fps。|
|-r|指定输出视频的分辨率。如 -r 640 360，表示输出视频的宽为640，高为360。|

### 功能描述  
> 首先介绍一下视频段（Segment）的概念：如果两个切片之间的时间间隔超过15秒，间隔时间内没有任何音频/视频信息（如果没有开启辅流模式，会忽略辅流信息），我们把这两个切片看作两个不同的Segment。其中，录制时间较早的切片看作前一个Segment的结束切片，录制时间较晚的切片看作后一个Segment的开始切片。

 - 分段模式（-m 0）
此模式下，脚本将每个uid下的录制文件按Segment合并。一个uid下的Segment被独立合并为一个文件。
            
-   合并模式（-m 1）
把同一个uid下的所有Segment段合并为一个音视频文件。可利用 -s 选项选择是否填充各个Segment之间的间隔。

### 输出文件命名规则
音视频文件：uid_timestamp_av.mp4

纯音频文件：uid_timestamp.m4a

其中，uid表示用户唯一标识；timestamp表示音视频开始录制的时间。
