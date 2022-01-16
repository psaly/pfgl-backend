from json import dumps

output = []

for segment in range(1, 4):
    with open("./segment" + str(segment) + ".txt") as f:
        line_num = -2
        week = 0
        for line in f:
            # print(line, line_num, week)
            matchup = {"segment": segment, "week": week}
            
            if line_num < 0:
                line_num+=1
                continue
            elif (line_num+1) % 6 == 0:
                if line_num > 0:
                    week += 1
                else:
                    line_num+=1
                    continue
            else :
                matchup["managers"] = line.strip().lower().split(" v ")
                output.append(matchup)
            line_num+=1
            
print(dumps(output))
