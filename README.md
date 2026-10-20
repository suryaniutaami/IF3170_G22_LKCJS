# IF3170_G22_LKCJS

Program optimasi pemuatan paket ke dalam truk menggunakan algoritma pencarian lokal. Program mendukung satu truk maupun armada beberapa truk dengan dimensi dan kapasitas yang dapat berbeda.

## Kebutuhan

- Python 3.10 atau lebih baru
- Matplotlib untuk visualisasi

Buat dan aktifkan virtual environment dari folder proyek, lalu pasang Matplotlib:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install matplotlib
```

Jika virtual environment sudah aktif, langkah pembuatan dan aktivasi tidak perlu diulang.

## Menjalankan lewat `main.py`

Dari folder utama proyek:

```bash
python3 src/main.py
```

Program akan meminta algoritma, seed, file input, parameter yang relevan, dan nama file output. Untuk Hill Climbing, pilih salah satu varian:

- Steepest Ascent
- Sideways Move
- Stochastic
- Random Restart

Sesudah algoritma selesai, program menanyakan apakah visualisasi ingin ditampilkan. Jika ya, gambar dibuka dan disimpan sebagai PNG.

Argumen dapat diberikan untuk melewati prompt yang nilainya sudah ditentukan. Contoh:

```bash
python3 src/main.py \
  --algorithm hill_climbing \
  --hc-variant sideways \
  --input basic_small.txt \
  --max-sideways 10 \
  --seed 42 \
  --output hasil_hill_climbing.json \
  --no-visualize
```

Contoh Simulated Annealing:

```bash
python3 src/main.py \
  --algorithm simulated_annealing \
  --input input_multi.txt \
  --max-iterations 5000 \
  --seed 42 \
  --output hasil_sa.json \
  --visualize
```

Argumen SA lanjutan meliputi `--initial-temperature`, `--cooling-rate`, `--min-temperature`, `--max-neighbor-attempts`, `--stuck-threshold`, `--target-acceptance`, dan `--temperature-samples`. Jika suhu awal tidak diberikan, program mengestimasinya dari sampel neighbor dengan target penerimaan langkah menurun 0,9 dan 100 sampel. Estimasi serta cara kalibrasinya dicatat dalam JSON. Jika sampel tidak menemukan langkah menurun, program memakai fallback berdasarkan skala nilai paket.

Contoh Genetic Algorithm:

```bash
python3 src/main.py \
  --algorithm genetic_algorithm \
  --input fleet_small.txt \
  --population 20 \
  --generations 50 \
  --seed 42 \
  --output hasil_ga.json \
  --no-visualize
```

Parameter khusus Hill Climbing tersedia melalui `--max-sideways`, `--max-iterations`, `--max-restarts`, dan `--target-value`. Seed default adalah `42`. Masukkan nama file input yang berada di folder `input/`; hasil JSON disimpan di folder `output/`. Nama PNG visualisasi mengikuti nama file JSON dan disimpan di `output/visualization/`.

Jika nama file output yang sama sudah ada, file JSON akan ditimpa.

Untuk menggandakan satu truk yang didefinisikan pada input menjadi beberapa truk identik, gunakan `--trucks`, misalnya:

```bash
python3 src/main.py --algorithm hill_climbing --hc-variant steepest --input input.txt --trucks 3 --seed 42 --output hasil_3trucks.json --no-visualize
```

Jika input sudah mendefinisikan beberapa truk, jumlah pada `--trucks` harus sama dengan jumlah truk tersebut.

## Input

Input disimpan sebagai teks di folder `input/`. Baris pertama menyatakan jumlah paket. Baris berikutnya berisi data paket, lalu minimal satu baris data truk.

Dua format baris paket yang didukung:

```text
id width depth height value weight fragile eta
id width depth height axis_x axis_y axis_z value weight fragile eta
```

Format pertama memakai orientasi awal `(x, y, z)`. Pada format kedua, `axis_x`, `axis_y`, dan `axis_z` menentukan orientasi awal dimensi paket. `fragile` bernilai `0` atau `1`.

Setiap baris truk menggunakan format:

```text
[id] width depth height max_capacity
```

ID truk opsional; jika tidak ditulis, program memberi ID `T1`, `T2`, dan seterusnya. Contoh input tersedia di `input/`.

Truk dalam armada diletakkan sepanjang sumbu X dengan jarak 2 unit. Posisi paket memakai koordinat global. Paket dihitung masuk truk bila seluruh baloknya berada di dalam satu truk; paket yang menembus dinding atau menjembatani dua truk tidak valid. Kapasitas diperiksa per truk. Objective utama adalah jumlah nilai paket yang berada di dalam truk.

## Runner algoritma terpisah

Skrip `run_*.py` tetap dapat dijalankan langsung. Jalankan dari folder `src/` karena runner tersebut membaca input relatif terhadap folder itu:

```bash
cd src
python run_hill_climbing.py --input input_multi.txt
python run_simulated_annealing.py --input input_multi.txt
python run_genetic_algorithm.py --input input_multi.txt
python run_visualization.py --algorithm steepest --input input_multi.txt
```

- `run_hill_climbing.py` menjalankan keempat varian Hill Climbing dan mencetak ringkasan ke terminal.
- `run_simulated_annealing.py` menjalankan tiga run dengan seed berurutan (default mulai dari 42), mengkalibrasi suhu awal seperti `main.py`, lalu menyimpan JSON dan plot PNG dengan nama yang menyertakan input dan seed. Gunakan `--seed` untuk mengatur seed awal.
- `run_genetic_algorithm.py` menjalankan eksperimen beberapa variasi populasi dan generasi, lalu menyimpan hasil JSON di `output/`.
- `run_visualization.py` menjalankan algoritma yang dipilih dan menampilkan visualisasi. Gunakan `--no-show` untuk hanya menyimpan gambar.
- `run_visual_scenarios.py` merender skenario visualisasi bawaan, bukan membaca file input.

Untuk pilihan algoritma dan parameter lengkap, jalankan skrip dengan `--help`, misalnya `python run_visualization.py --help`.

## Menjalankan tes

Dari folder utama proyek:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Untuk tes multi-truk saja:

```bash
python3 -m unittest discover -s tests -p "test_multi_truck.py"
```

## Anggota
| Name | Student ID |
| --- | --- |
| Aziza Dharma Putri | 13524017 |
| Suryani Mulia Utami | 13524042 |
| Alya Nur Rahmah | 13524081 |
