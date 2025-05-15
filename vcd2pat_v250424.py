import re
import os
import bisect

#第一个函数：给每个#开头的行前面添加一行$end
def add_end_line(vcd_file_path, modified_file_path):
    modified_lines = []

    with open(vcd_file_path, 'r') as file:
        for line in file:
            if re.match(r'^#', line):
                # 修改匹配的行
                modified_line = '$end\n' + line
                modified_lines.append(modified_line)
            else:
                # 如果不需要修改，直接添加原行
                modified_lines.append(line)

            # 写入修改后的行到新文件
    with open(modified_file_path, 'w') as file:
        file.writelines(modified_lines)


#第二个函数：从vcd转出信号名和各个时刻的信号值，整理成pattern格式的预览版
def parse_vcd(modified_file_path, go_smaple_path):
    signals = {}  # dec端口说明中的GPIO跟标识符对应起来
    #timescale = None
    pins = []

    with open(go_smaple_path, 'w') as go_smaple_file:
        with open(modified_file_path) as file:
            for line in file:
                #if '$timescale' in line:
                    #next_line = next(file).strip()
                    #timescale = re.sub(r'\d+', '', next_line)

                if '$var' in line:
                    parts = line.split()
                    signals[parts[3]] = {'name': parts[4], 'value': None}  # 键为标识符； 新的字典值为两个键值对，name为实际端口名（GPIO）
                    pins.append(parts[4])

                if '$enddefinitions' in line:
                    go_smaple_file.write(' '.join(pins) + '\n')  # 写入第一行

                if re.match(r'^#', line):  # '^'是一个锚定符，表示匹配必须发生在字符串的开始位置
                    time = line.strip()[1:]

                    while True:
                        val_line = next(file, '').strip()

                        if not val_line or val_line.startswith('$end'):
                            break
                        if val_line.startswith(('0', '1', 'z', 'x')):
                            val, sig = val_line[0], val_line[1:]  # val为value实际的值； sig为对应的标识符；   这一句为标准的python解包语法
                            for key, signal in signals.items():  # key中赋值的是标识符； signal中赋值的是新的字典值，即为'name'和'value'
                                if key == sig:
                                    signal['value'] = val
                                    break

                    value_list = [sub_dict['value'] for sub_dict in signals.values() if 'value' in sub_dict]
                    value_list.insert(0, time)
                    go_smaple_file.write(' '.join(map(str, value_list)) + '\n')



#第三个函数：采样函数（按照自定义的偏移量、周期以及采样率来采样）
def generate_resampled_signals(go_sample_path, offset, cycle, sampling_rate):
    with open(go_sample_path, 'r') as file:
        ports = file.readline().strip().split(' ')
        yield ' '.join(ports) + '\n'

        times = []
        signals = []
        for line in file:
            row = line.strip().split(' ')
            times.append(float(row[0]))
            signals.append(row[1:])

        n = 0
        while True:
            sp = offset + (sampling_rate + n) * cycle
            if sp >= times[-1]:
                break

            # 使用二分查找找到 sp 的插入点
            i = bisect.bisect_right(times, sp)
            if i > 0:
                yield ' '.join(signals[i - 1]) + '\n'

            n += 1


#第四个函数：保存采样结果
def save_sample_result(go_sample_path, sample_OK_output_path, offset, cycle, sampling_rate):
    with open(sample_OK_output_path, 'w') as file:
        for line in generate_resampled_signals(go_sample_path, offset, cycle, sampling_rate):
            file.write(line)


#第五个函数：根据dec输入文件来确定每个pin的输入输出类型
def dummy():
    in_pins = []
    out_pins = []
    io_pins = []
    io_OEN_pins = []
    with open(dummy_path, 'r') as dummy_file:
        for line in dummy_file:
            pins = line.split()
            if len(pins) >= 2:  # 确保有足够的部分
                part_name = str(pins[0])
                part_type = str(pins[1])
            if part_type == 'OUT':
                out_pin = part_name
                out_pins.append(out_pin)
                #print(out_pins)
            elif part_type == 'IN':
                in_pin = part_name
                in_pins.append(in_pin)
                #print(in_pins)
            elif part_type == 'IO':
                io_pin = part_name
                io_OEN_pin = part_name + '_OEN'
                io_pins.append(io_pin)
                io_OEN_pins.append(io_OEN_pin)
                #print(io_pins)
                #print(io_OEN_pins)
    return out_pins, in_pins, io_pins, io_OEN_pins  #返回4个列表


#第六个函数：整理出每种类型的pin的位置索引
def ctl_sig():
    out_site = []   #site里面存放的是所有的index
    in_site = []
    io_site = []
    io_OEN_site = []
    with open(sample_OK_output_path)as sam_file:
        sam_pins = sam_file.readline().strip().split()  #采样文件第一行pin名存为一个列表
        fina_pin_nums = len([fpin for fpin in sam_pins if "_OEN" not in fpin])
        for index, value in enumerate(sam_pins):
            for out_pin in out_pins:
               if out_pin == value:
                   out_site.append(index)
            for in_pin in in_pins:
               if in_pin == value:
                   in_site.append(index)
            for io_pin in io_pins:
                if io_pin == value:
                    io_site.append(index)
            for io_OEN_pin in io_OEN_pins:
                if io_OEN_pin == value:
                    io_OEN_site.append(index)
    return fina_pin_nums, out_site, in_site, io_site, io_OEN_site     #返回4个包含索引值的列表


#第七个函数：根据端口类型修改信号值（in类型将z改为x；out类型将1改为H,0改为L；io类型根据对应的OEN的1或0，修改为H或L）
def modify_file(sample_OK_output_path, fina_pin_nums, out_site, in_site, io_site, io_OEN_site):
    with open(sample_OK_output_path, 'r') as file:
        with open(finally_file, 'w') as temp_file:
            line_count = 0
            for line in file:
                line_count += 1
                if line_count >= 2:
                    line = line.strip().split()
                    modified_line = list(line)
                    #print(modified_line)
                    for out_index in out_site:
                        if modified_line[out_index] == '1':
                            modified_line[out_index] = 'H'
                        elif modified_line[out_index] == '0':
                            modified_line[out_index] = 'L'
                        elif modified_line[out_index] == 'z':
                            modified_line[out_index] = 'X'
                        elif modified_line[out_index] == 'x':
                            modified_line[out_index] = 'X'

                    for in_index in in_site:
                        if modified_line[in_index] == 'z':
                            modified_line[in_index] = 'X'
                        elif modified_line[in_index] == 'x':
                            modified_line[in_index] = 'X'

                    for io_index, io_OEN_index in zip(io_site, io_OEN_site):
                        if modified_line[io_OEN_index] == '0':
                            if modified_line[io_index] == 'z':
                                modified_line[io_index] = 'X'
                            elif modified_line[io_index] == '0':
                                modified_line[io_index] = 'L'
                            elif modified_line[io_index] == '1':
                                modified_line[io_index] = 'H'
                            elif modified_line[io_index] == 'x':
                                modified_line[io_index] = 'X'
                        elif modified_line[io_OEN_index] == '1':
                            if modified_line[io_index] == 'z':
                                modified_line[io_index] = 'X'
                            elif modified_line[io_index] == 'x':
                                modified_line[io_index] = 'X'

                    modified_line = ''.join(modified_line)#将 modified_line 列表中的所有字符串元素连接成一个单一的字符串，中间没有任何分隔符（因为连接符是空字符串 ''），区别于modified_line = str(modified_line)
                    if len(modified_line) > fina_pin_nums:
                        modified_line = modified_line[:fina_pin_nums]     # 删除OEN的内容
                    temp_file.write(''.join(modified_line) + '\n')
                else:
                    temp_file.write(line)


#第八个函数：将信号值按10个一组整齐排列
def trimming():
    with open(finally_file, 'r') as file:
        lines = file.readlines()

        with open(finally_file, 'w') as trimmed_file:
            for line in lines[1:]:
                trimmed_line = ''
                for i, char in enumerate(line.strip()):
                    trimmed_line += char
                    if (i + 1) % 10 == 0:
                        trimmed_line += ' '
                trimmed_line = '*' + trimmed_line.strip() + '* TS1;\n'
                trimmed_file.write(trimmed_line)


#第九个函数：删除中间过渡文件
def remove_staging_files(modified_file_path, go_sample_path, sample_OK_output_path):
   # 文件路径列表
   file_paths = [modified_file_path, go_sample_path, sample_OK_output_path]
   # 删除文件
   for file_path in file_paths:
       if os.path.exists(file_path):
         os.remove(file_path)
         print(f"已删除文件: {file_path}")
       else:
         print(f"文件不存在: {file_path}")

#文件路径
vcd_file_path = "D:\\R069_ate_vcd\\R069_output.vcd"          #请在此处添加原始的vcd文件路径
modified_file_path = "D:\\modified_vcd.pat"      #已添加$end后的vcd (该文件作为中间文件，最后会删除)
go_sample_path = "D:\\go_smaple.pat"             #取出vcd转出信号名和各个时刻的信号值的文件  (该文件作为中间文件，最后会删除)
sample_OK_output_path = "D:\\sam_OK_output.pat"    #采样数据保存文件  (该文件作为中间文件，最后会删除)
dummy_path = "D:\\judge.dec"                  #此处添加规定信号类型的输入文件
#finally_file = 'D:\\finally_OK_file.pat'
finally_file = os.path.splitext(vcd_file_path)[0] + ".pat"#最终生成的vcd2pat文件，跟输入的vcd文件在同一路径下

#按照自定义的偏移量、周期以及采样率来采样， 默认单位为 ps
offset = 16664
cycle = 33328
sampling_rate = 0.8

# 调用函数
add_end_line(vcd_file_path, modified_file_path)
parse_vcd(modified_file_path, go_sample_path)
save_sample_result(go_sample_path, sample_OK_output_path, offset, cycle, sampling_rate)
out_pins, in_pins, io_pins, io_OEN_pins = dummy()
fina_pin_nums, out_site, in_site, io_site, io_OEN_site = ctl_sig()
modify_file(sample_OK_output_path, fina_pin_nums, out_site, in_site, io_site, io_OEN_site)
trimming()
remove_staging_files(modified_file_path, go_sample_path, sample_OK_output_path)