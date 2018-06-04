# kcem

An Ontology tool kit which is based on [kcm](https://github.com/udicatnchu/new_kcm) and [kem](https://github.com/udicatnchu/kem)

It has `311612` distinct concepts and `1221087` distinct concept-instances

## Info of Wiki Dumps

```
Database changed
mysql> SELECT COUNT(*) FROM categorylinks;
+----------+
| COUNT(*) |
+----------+
| 12490991 |
+----------+
1 row in set (10.10 sec)

mysql> SELECT COUNT(*) FROM page;
+----------+
| COUNT(*) |
+----------+
|  5380929 |
+----------+
1 row in set (5.68 sec)

mysql> 

```


## Install

* (Recommended): Use [docker-compose](https://github.com/udicatnchu/udic-nlp-api) to install

## Manually Install

If you want to integrate `kcem` into your own django project, use manually install.

* `pip install kcem`

### Config
Cause this is a django app

so need to finish these django setups.

1. settings.py：

  ```python
  INSTALLED_APPS = [
      'kcem'
       ...
  ]
  ```
2. urls.py：  

  ```python
  import kcem.urls
  urlpatterns += [
      url(r'^kcem/', include(kcem.urls))
  ]
  ```

3. `python3 manage.py buildkcem --lang <lang, e.g., zh or en or th>`
4. fire `python manage.py runserver` and go `127.0.0.1:8000/` to check whether the config is all ok.

## API

1. Get correlated keywords：_`/kcem`_
    - keyword
    - num (default=10)
    - example1：<http://udiclab.cs.nchu.edu.tw/kcem?keyword=周杰倫&lang=zh>

        ```json
        {
          "origin": "周杰倫",
          "similarity": 1,
          "value": [
            [
              "臺灣男歌手",
              0.1077329254516259
            ],
            [
              "臺灣創作歌手",
              0.08618136696067945
            ],
            [
              "臺灣作詞家",
              0.08453908870383998
            ],
            [
              "臺灣男演員",
              0.07853875803243504
            ],
            [
              "客家裔臺灣人",
              0.07775312164574238
            ],
            [
              "臺灣作曲家",
              0.06795213648026219
            ],
            [
              "臺灣億萬富豪",
              0.06205651770108215
            ],
            [
              "臺灣新教徒",
              0.06011534659254377
            ],
            [
              "以臺灣音樂家命名的分類",
              0.04864802203579143
            ],
            [
              "臺灣電視主持人",
              0.04471306738037418
            ],
            [
              "叱吒樂壇我最喜愛的歌曲得主",
              0.035176987895887926
            ],
            [
              "全球華語歌曲排行榜最受歡迎男歌手",
              0.03386244943947794
            ],
            [
              "金曲獎演奏類最佳專輯製作人獎獲得者",
              0.03333042924853456
            ],
            [
              "華語流行音樂歌手",
              0.027811995551754405
            ]
          ],
          "key": "周杰倫"
        }
        ```

### Evaluate

`python3 manage.py evaluate --lang <zh or other supported language>`

## Contributors

- **張泰瑋** [david](https://github.com/david30907d)

## License

This package use `GPL3.0` License.

# KCEM experiments

kcem有兩個參數，kcm取幾個、kem取幾個，本實驗使用[google的知識圖譜](https://github.com/UDICatNCHU/Open-Sentiment-Training-Data/blob/master/Ontology_from_google.json)約500筆做測試

為了畫成二維的圖，把kcm的參數表示成顏色、loss為y軸、kem數量為x軸

參數的範圍從2~30 `range(2, 30, 2)`


1. 舊的kcem跟取第一段維基百科去斷詞，而且不是紀錄頻率而是用set儲存所做出來的kcem效果的比較
![我的kcem_compare_kcem.png](picture/我的kcem_compare_kcem.png)
2. hybrid的loss V.S. kcem的loss:
![hybridVSkcem.png](picture/hybridVSkcem.png)
3. hybrid 的loss V.S. new method的loss:
![hybridVSnew.png](picture/hybridVSnew.png)
4. 四種版本的kcem比較:
同一種方法但是不同kcm、kem參數的loss都畫成同一顏色的線
![4個趨勢.png](picture/4個趨勢.png)
5. 四種全部都取平均:
同一種方法但是不同kcm、kem參數的loss都取平均,畫成同一顏色的線
![4個平均.png](picture/4個平均.png)

### 10/13小結論：

`new method`因為只取第1段的表現比較不穩定，所以採用hybrid方法

new method相關的實驗程式放在[new_kcem_method](new_kcem_method)

將用hybrid的min：`kcm:22 kem:12 loss:21.458033917027294` 這組參數當作目前最佳的`is-a`去做後續應用