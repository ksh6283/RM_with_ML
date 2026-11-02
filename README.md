# Problem of Machine Learning approaches for Resource mangement system
-----------

본 레포는 MSA의 Resource Management 연구 실험 프레임워크며 아래의 두가지 선행 연구의 공개 코드와 논문을 기반으로 구현되었습니다.

| 연구 | 논문 | 공개 코드 |
|---|---|---|
| **Erms**: Efficient Resource Management for Shared Microservices with SLA Guarantees (ASPLOS '23) | [doi:10.1145/3567955.3567964](https://doi.org/10.1145/3567955.3567964) | [GitHub](https://github.com/Cloud-and-Distributed-Systems/Erms) / [Zenodo](https://doi.org/10.5281/zenodo.7220659) |
| **Derm**: SLA-aware Resource Management for Highly Dynamic Microservices (ISCA '24) | [doi:10.1109/ISCA59077.2024.00039](https://doi.org/10.1109/ISCA59077.2024.00039) | [GitHub](https://github.com/liaochan/Derm) / [Zenodo](https://doi.org/10.5281/zenodo.10947677) |

## k8s 클러스터 세팅

> 기존 실험 환경의 설정 스크립트(삭제된 `vagrant/*`, `calico-node.yaml`)와 프레임워크 코드에서 역으로 정리한 내용입니다.

| 항목 | 값 |
|---|---|
| OS | Ubuntu 22.04 |
| Kubernetes | kubeadm / kubelet / kubectl `1.30.1-1.1` |
| CRI | containerd.io `1.6.28-1` (`SystemdCgroup = true`) |
| CNI | Calico v3.25.0 (IPIP `Always`, VXLAN `Never`) |
| Pod CIDR | `172.16.0.0/16` |
| 노드 | control-plane 1 + worker 2 (노드 이름은 `.env`의 `NODES_FOR_*`와 일치해야 함) |

### 1. 모든 노드 공통
```bash
sudo swapoff -a && sudo sed -i.bak -r 's/(.+swap.+)/#\1/' /etc/fstab
sudo modprobe br_netfilter
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# kubernetes / docker(containerd) apt repo
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list

sudo apt-get update
sudo apt-get install -y kubelet=1.30.1-1.1 kubeadm=1.30.1-1.1 kubectl=1.30.1-1.1 containerd.io=1.6.28-1
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
sudo systemctl restart containerd && sudo systemctl enable containerd
sudo systemctl enable --now kubelet
```

### 2. control-plane
```bash
sudo kubeadm init --pod-network-cidr=172.16.0.0/16 \
  --apiserver-advertise-address=<control-plane IP> \
  --cri-socket=unix:///run/containerd/containerd.sock
mkdir -p ~/.kube && sudo cp /etc/kubernetes/admin.conf ~/.kube/config && sudo chown $(id -u):$(id -g) ~/.kube/config

# Calico: calico.yaml의 calico-node env에 노드 간 통신 NIC를 고정 (멀티 NIC 환경)
#   CALICO_IPV4POOL_CIDR=172.16.0.0/16, IP_AUTODETECTION_METHOD=can-reach=<게이트웨이 IP>
curl -LO https://raw.githubusercontent.com/projectcalico/calico/v3.25.0/manifests/calico.yaml
kubectl apply -f calico.yaml
```

### 3. worker
```bash
sudo kubeadm join <control-plane IP>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
# token 재발급: kubeadm token create --print-join-command
```

### 4. 프레임워크 요구사항
- **스케줄링**: affinity는 `kubernetes.io/hostname` 라벨로 노드를 고르고 인프라 Pod는 `node-role.kubernetes.io/control-plane:NoSchedule` toleration이 있음 → control-plane 노드도 `NODES_FOR_INFRA`에 넣을 수 있음
- **kubeconfig**: `deployment/deployer.py`가 `config.load_kube_config()` + `kubectl`을 사용하므로 실행 머신에 `~/.kube/config` 필요
- **Prometheus** (선택, `prometheus_host`): `kube-prometheus-stack`을 NodePort `30090`으로 노출
  ```bash
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace \
    --set prometheus.service.type=NodePort --set prometheus.service.nodePort=30090
  ```
  `utils/prometheus.py`가 cAdvisor 메트릭(`container_cpu_usage_seconds_total`)과 recording rule(`node_namespace_pod_container:container_memory_working_set_bytes`)을 사용. node 단위 쿼리의 `kube_pod_container_resource_limits_cpu_cores`는 kube-state-metrics v1 이름이라 v2 이상에서는 빈 값 (추정)
- **Jaeger**: 앱별 `non-test/jaeger_*.yaml`로 함께 배포 (UI NodePort `30095`). 별도 설치 불필요
- **wrk2** (hotel 워크로드): 동봉 바이너리가 `libssl.so.1.1`에 링크되어 있음 → Ubuntu 22.04에서는 `libssl1.1` 수동 설치 필요

## 로컬 설정 (`main/.env`)

클러스터 주소, 노드 이름, 계정/토큰은 git에 올라가지 않는 `main/.env`에서 읽습니다.
```bash
cp main/.env.example main/.env   # 값 채우기
```
- Python: `main/local_env.py`가 import 시 `.env`를 `os.environ`에 로드 (이미 설정된 환경변수가 우선)
- `configs/*.yaml`, `yamlRepository/**/*.yaml`: `${VAR}` / `${VAR:-default}`를 로딩 시 치환. 그래서 `kubectl apply -f`로 직접 적용하면 안 되고, 직접 적용하려면 `envsubst`를 거쳐야 함
- wrk2 lua: `os.getenv()`로 읽음. `profiling.py`에서 실행하면 환경이 상속되고, 직접 실행할 때는 `set -a; source main/.env; set +a`


## Benchmark 배포 (train-ticket / hotelReservation)

모든 명령은 `main/`에서 실행합니다. 배포는 소스 빌드가 아니라 Docker Hub에 올라간 이미지를
`main/yamlRepository/<app>/` 의 yaml로 띄우는 방식입니다.

대상 앱은 환경변수 `ERMS_APP`(기본값 `train`)으로 선택하며, `configs/<app>-global.yaml`, `configs/<app>-testing.yaml`이 로드됩니다.

| 항목 | train-ticket | hotelReservation |
|---|---|---|
| `ERMS_APP` | `train` | `hotel` |
| namespace | `train-ticket` | `hotel-reserv` |
| yaml 경로 | `yamlRepository/trainTicket` | `yamlRepository/hotelReservation` |
| 진입점 (NodePort) | `ts-ui-dashboard` : 32677 | `frontend` : 30096 |
| Jaeger UI (NodePort) | 30095 | 30095 |
| 인프라 이미지 | `mongo:3.4`, `mysql`, `redis`, `jaegertracing/all-in-one:1.54` | `nicklin9907/erms:mongo`, `nicklin9907/erms:memcached`, `consul:1.8.4`, `jaegertracing/all-in-one:1.54` |
| 워크로드 | Python (`workloadGenerator/trainticketWorkload.py`) | wrk2 + lua (`wrk2/scripts/hotel-reservation/*.lua`) |

### 0. 사전 설정
1. `main/.env`
   - `NODES_FOR_TEST`, `NODES_FOR_INFRA`, `FRONTEND_NODE`: 실제 노드 이름(`kubectl get nodes`)과 일치해야 함. 다르면 affinity 때문에 Pod가 Pending 상태로 남음
   - `CLUSTER_HOST`: 서비스/Jaeger NodePort에 접근할 노드 IP (`configs/<app>-testing.yaml`의 url, jaeger_host)
   - `PROMETHEUS_URL`: hotel만 사용. train은 `configs/train-global.yaml`에서 `prometheus_host: null` (트레이스만 수집)
2. namespace 생성 (deployer가 자동 생성하지 않음)
   ```bash
   kubectl create namespace train-ticket   # 또는 hotel-reserv
   kubectl create namespace interference   # CPU/Memory 간섭 Pod용
   ```

### 1. 배포
`main.py` 하단의 `full_init(...)` 중 대상 앱 한 줄만 주석 해제 후 실행합니다.
`ERMS_APP`과 `full_init`의 앱 이름이 반드시 같아야 합니다 (다르면 다른 앱의 yaml이 배포됨).
```python
# full_init("hotel", 30096)
full_init("train", 32677)
```
```bash
export ERMS_APP=train      # hotel 배포 시 ERMS_APP=hotel
python3 main.py
```
`full_init` 동작:
1. `non-test/` (DB, 캐시, Jaeger 등)에 namespace와 `nodes_for_infra` affinity를 넣어 `tmp/infra-<ns>/`에 저장한 뒤, 삭제 후 재생성
2. `test/` (앱 서비스)에 namespace, `pod_spec`(CPU/Mem limit), `nodes_for_test` affinity, `imagePullPolicy: IfNotPresent`를 넣어 `tmp/testing-<ns>/`에 저장한 뒤 배포하고 Ready까지 대기

확인:
```bash
kubectl get pods -n train-ticket -o wide   # 또는 hotel-reserv
curl http://$CLUSTER_HOST:32677            # hotel: 30096
```

## 프로파일링 (데이터 수집)
```bash
chmod +x wrk2/wrk          # hotel만 해당
export ERMS_APP=train      # 또는 hotel
python3 profiling.py       # start_test(continues=True): 기존 데이터에 이어서 저장
```
- 테스트할 서비스는 `<app>-testing.yaml`의 `services`에 지정 (train: `Booking` / hotel: `Search`, `Recommendation`, `Login`, `Reservation`)
- 결과는 `<app>-global.yaml`의 `data_path` (`data_train/`, `data_hotel/`)에 저장
- `profiling.py` 안의 `app = "train"`은 설정 로딩에 영향이 없음. 반드시 `ERMS_APP`으로 지정

수집 결과 구조 (`dataCollector/OfflineProfilingDataCollector.py`):
```
<data_path>/offlineTestResult/
├─ <throughput>/epoch_<repeat>/simple/raw_data.csv    # 단순 그래프 trace (span 단위)
├─ <throughput>/epoch_<repeat>/complex/raw_data.csv   # 복합 그래프 trace
├─ latencyByPod.csv, originalData.csv, spanRelationships.csv, db.csv
```
`raw_data.csv` 주요 컬럼: `traceId`, `parentId`, `parentMS`, `childMS`, `parentDuration`, `childDuration` (µs)

## 피팅 및 자원 최적화

수집한 trace로 마이크로서비스별 지연 분포를 피팅하고, 그 파라미터로 SLA를 만족하는 최소 컨테이너 수를 계산합니다.
코드는 `main/Derm-master/`에 있으며 현재 hotelReservation 기준으로 작성되어 있습니다.

```
offlineTestResult/*/raw_data.csv
   │ ① print_ms_info.py     서비스 구성, ms_dict 계산
   │ ② curve_cdf.py         서비스·워크로드별 지수분포 CDF 피팅 → data/hotel-reserv/<ms>.csv
   │ ③ line_fit_exp.py      워크로드-λ 선형회귀 → data/line_fit.csv
   │    (복사)              → allocation/data/all_pars.csv
   ▼ ④ resourceAllocation.py SLA·워크로드별 최적 컨테이너 수
```

추가 의존성: `Derm-master/requirements.txt` 외에 `scipy`, `ipdb` 필요
```bash
pip install -r Derm-master/requirements.txt scipy ipdb
```

### ① 서비스 구성 분석 — `AE/scripts/print_ms_info.py`
```bash
cd main
python3 AE/scripts/print_ms_info.py
```
- 입력: `data_root`(코드 상단)의 `60/epoch_0/{simple,complex}/raw_data.csv`. 실제 수집 경로(예: `data_hotel/offlineTestResult`)로 수정
- `container_numbers`: 각 서비스의 실제 Pod 수를 직접 입력 (`kubectl get pods -n hotel-reserv`)
- 출력:
  - parent / child 서비스 목록
  - simple 전용(`simple_non_shared`) / complex 전용(`complex_non_shared`) 서비스
  - `ms_dict` (Pod당 평균 호출 비율 = `(9·simple 호출 + 1·complex 호출) / 컨테이너 수`)
  - 출력값을 ②의 같은 이름 변수에 붙여넣습니다.

### ② 지연 분포 피팅 — `Derm-master/profiling/performance_model/curve_cdf.py`
각 서비스의 순수 처리 지연(자식 호출 시간 제외)을 `F(x) = 1 - exp(-λx)`로 curve fit하고, MLE(`λ = 1/평균`)와 KL divergence를 비교합니다.
```bash
cd main/Derm-master/profiling/performance_model
python3 curve_cdf.py
```
실행 전 수정:
- `.env`의 `DERM_DATA_PATH`: 수집 데이터 경로 (`.../offlineTestResult`)
- `parent_services`, `child_services`, `complex_non_shared`, `simple_non_shared`, `ms_dict`: ①의 결과
- `collect_parameters()` 안의 `workloads = [30, 60]`: 실제 수집한 throughput 디렉토리 이름
- `get_latency*()`의 `range(0, 3)`: 실제 epoch 수 (`<app>-testing.yaml`의 `repeats`가 `[0, 1]`이면 `range(0, 2)`)

출력 (실행 디렉토리 기준):
- `data/hotel-reserv/<ms>.csv`: `fit_pars`, `ml_pars`, `kl_fit`, `kl_ml`, `workloadPerPod`, `latency_range`, `skew`, `data_num`, `p95`
- `figures/<ms>/<workload>.png`: 실측 CDF vs 피팅 CDF

### ③ 워크로드-λ 선형회귀 — `Derm-master/profiling/performance_model/line_fit_exp.py`
②의 `workloadPerPod`와 `fit_pars`/`ml_pars`를 `λ = a·w + b`로 회귀해 자원 최적화 입력 파라미터를 만듭니다.
```bash
# ②와 같은 디렉토리에서 실행 (data/hotel-reserv/*.csv를 읽음)
python3 line_fit_exp.py
cp data/line_fit.csv ../../allocation/data/all_pars.csv
```
실행 전 수정 (파일 하단 하드코딩 값):
- `ms_list`: 서비스 목록
- `chain`: 각 서비스가 속한 그래프 (`1`=simple, `2`=complex, `[1,2]`=공유)
- `invoke_times`: 그래프별 호출 횟수 `[simple, complex]`
- `pod_num`: Pod 수
- `graph_ratio`: `[simple 비율, complex 비율]`


출력 `data/line_fit.csv` 컬럼: `chain`, `ms`, `n`(호출 횟수), `percentage`(그래프 비율), `a1`, `b1`(fit 회귀), `a2`, `b2`(MLE 회귀), `s`(skew), `pod_num`

### ④ 자원 최적화 — `Derm-master/allocation/resourceAllocation.py`
③의 파라미터로 그래프별 E2E 지연이 SLA(P95)를 만족하는 범위에서 총 컨테이너 수를 최소화합니다.
반복 최적화(λ, ρ, π 갱신 30회)를 하고, `end2endLatencyUpdate.py`로 각 반복의 SLA 만족 여부를 검증합니다.
```bash
cd main/Derm-master/allocation
python3 -W ignore resourceAllocation.py
```
- 입력:
  - `data/all_pars.csv`: ③의 출력
  - `data/workload_ceil.csv`: 대상 워크로드 목록 (`workload` 컬럼)
- 조정 변수 (파일 하단 / `__init__`):
  - `sla_list = [550]`: SLA (ms)
  - `ratio=0.5`: simple 그래프 비율 (complex = 1 - ratio)
  - `profilingWorkload = 40`: 프로파일링 시 기준 워크로드
  - `cutoffLambda`, `miniWorkload`: λ·Pod당 워크로드 탐색 범위
- 출력: 워크로드·SLA마다 마이크로서비스별 할당 컨테이너 수(올림)를 출력합니다. 이 값을 `<app>-global.yaml`의 `replicas`에 반영해 재배포합니다.

### (선택) 동적 그래프 예측 — `Derm-master/profiling/prediction_model/`
Alibaba cluster trace로 호출 그래프 분포를 예측하는 모델입니다. 위 ①~④와는 독립적으로 실행됩니다. 데이터와 모델은 직접 받아야 합니다.
```bash
cd main/Derm-master/profiling/prediction_model
./fetch_all.sh start_date=0d0 end_date=0d12   # Alibaba 2022 trace 다운로드 (<일>d<시> 형식, 12시간 단위)
cd pre-processing
python3 filter_disconnected_trace_data.py   # Unknown/Unavailable 제거, CSV → Parquet
python3 split_trace_graph.py                # 그래프 분포 상위 36종 분류
python3 split_trace_argument.py             # argument 분포 상위 12종 분류
cd ..
python3 make_npy.py                         # data/graph_predict/*.npy 생성
python3 predict.py train                    # models/graph_predict.pt 저장
python3 predict.py test
```

### train-ticket 소스
**수정본 (`ksh6283/ts-*` 이미지의 빌드 소스)**
- [vaquarkhan/train-ticket](https://github.com/vaquarkhan/train-ticket/tree/master) 기반 수정본
- 태그 `archive/train-ticket-sources`의 `main/train-ticket-hskim/`에 보관
```bash
# 레포 루트에서
git checkout archive/train-ticket-sources -- main/train-ticket-hskim
git restore --staged main/train-ticket-hskim   # git 추적 대상에서 다시 제외
cd main/train-ticket-hskim && mvn clean package
./docker_build_all.sh     # 스크립트 안의 BASE_DIR, version 값을 먼저 수정
```
이미지를 새로 빌드했다면 `yamlRepository/trainTicket/test/*-Deployment.yaml`의 이미지 태그를 갱신합니다.

**원본 (참고용)**
- [FudanSELab/train-ticket `jaeger` 브랜치](https://github.com/FudanSELab/train-ticket/tree/jaeger) @ `cab7d81`
- 원본 대비 변경: `ts-contacts-service/Dockerfile`, `ts-verification-code-service/Dockerfile`의 `FROM java:8-jre` → `FROM openjdk:8-jre` (`java` 이미지 deprecated)
```bash
# 레포 루트에서
git clone -b jaeger https://github.com/FudanSELab/train-ticket.git && cd train-ticket
git checkout cab7d8195025c571f86278f9f56f3838943dbaa2
perl -pi -e 's/^FROM java:8-jre/FROM openjdk:8-jre/' \
  ts-contacts-service/Dockerfile ts-verification-code-service/Dockerfile
```

