#------------------------------------------------#
#   进行训练前需要利用这个文件生成cls_train.txt
#------------------------------------------------#
import os

if __name__ == "__main__":
    #---------------------#
    #   训练集所在的路径
    #---------------------#
    datasets_path   = ""

    list_file = open('model_data\lfw_pair.txt', 'w', encoding='utf-8')
    cls_id = 0
    
    # 遍历第一层文件夹 (如: face_dataset_23人工智能1班)
    for dir1 in sorted(os.listdir(datasets_path)):
        dir1_path = os.path.join(datasets_path, dir1)
        if not os.path.isdir(dir1_path):
            continue
        
        # 遍历第二层文件夹 (如: 23人工智能1班)
        for dir2 in sorted(os.listdir(dir1_path)):
            dir2_path = os.path.join(dir1_path, dir2)
            if not os.path.isdir(dir2_path):
                continue
            
            # 遍历 train 文件夹
            train_path = os.path.join(dir2_path, "test")
            if os.path.isdir(train_path):
                # 遍历每个人物文件夹 (如: 10_张创)
                for person_name in sorted(os.listdir(train_path)):
                    person_path = os.path.join(train_path, person_name)
                    if not os.path.isdir(person_path):
                        continue
                    
                    # 遍历该人物的所有图片
                    for photo_name in os.listdir(person_path):
                        photo_path = os.path.join(person_path, photo_name)
                        if os.path.isfile(photo_path):
                            list_file.write(str(cls_id) + ";" + os.path.abspath(photo_path))
                            list_file.write('\n')
                    
                    cls_id += 1
    
    list_file.close()
    print(f"生成了 {cls_id} 个类别的训练数据")
