# Problem of Machine Learning approaches for Resource mangement system
-----------

본 레포는 MSA의 Resource Management 연구 실험 프레임워크며 아래의 두가지 선행 연구의 공개 코드와 논문을 기반으로 구현되었습니다.

| 연구 | 논문 | 공개 코드 |
|---|---|---|
| **Erms**: Efficient Resource Management for Shared Microservices with SLA Guarantees (ASPLOS '23) | [doi:10.1145/3567955.3567964](https://doi.org/10.1145/3567955.3567964) | [GitHub](https://github.com/Cloud-and-Distributed-Systems/Erms) / [Zenodo](https://doi.org/10.5281/zenodo.7220659) |
| **Derm**: SLA-aware Resource Management for Highly Dynamic Microservices (ISCA '24) | [doi:10.1109/ISCA59077.2024.00039](https://doi.org/10.1109/ISCA59077.2024.00039) | [GitHub](https://github.com/liaochan/Derm) / [Zenodo](https://doi.org/10.5281/zenodo.10947677) |


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
1. `configs/<app>-global.yaml`
   - `nodes_for_test`, `nodes_for_infra`: 실제 노드 이름(`kubectl get nodes`)과 일치해야 함. 다르면 affinity 때문에 Pod가 Pending 상태로 남음
   - `prometheus_host`: Prometheus 주소. 없으면 `null` (트레이스만 수집)
2. `configs/<app>-testing.yaml`
   - `workload_config.services.*.url`, `collector_config.jaeger_host`: `http://<노드 IP>:<NodePort>`
3. namespace 생성 (deployer가 자동 생성하지 않음)
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
curl http://<노드 IP>:32677                # hotel: 30096
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

