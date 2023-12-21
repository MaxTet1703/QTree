# CLI для сжатия изображения
### Описание
Это консольное приложение позволяет создавать в зависимости от глубины сжатые изображения и сохранять результат в директории results.
Также данное приложение позволяет создавать gif-файл с сжатыми изображениями, разной глубины
### Пример работы
Создание сжатого изображения
```commandline
python main.py --image dataset/photo_two.jpg -d 3
```
Создание gif-файла
```commandline
python main.py --image dataset/photo_two.jpg -d 3 --gif
```
### Результаты
![](https://github.com/MaxTet1703/QTree/blob/main/results/photo_one.gif)
![](https://github.com/MaxTet1703/QTree/blob/main/results/photo_two.gif)