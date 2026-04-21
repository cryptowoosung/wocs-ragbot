# source_docs MANIFEST

- **복사 일시**: 2026-04-21 15:20~15:21 (GMT+9)
- **중복 제거**: 2026-04-21 15:30 (FITI 내수도-1.PDF 삭제, 상세는 `DEDUPE_LOG.md`)
- **총 파일**: 27개 (초기 28개 → 1개 중복 제거)
- **총 용량**: 약 39 MB
- **원본 기준**: (로컬 전용, 저장소 외)

## 폴더 요약

| 폴더 | 파일 수 |
|---|---|
| `catalog/` | 1 |
| `brochure/` | 1 |
| `product_brochure/` | 16 |
| `fiti/` | 9 |
| **합계** | **27** |

---

## catalog/ (1개)

| 파일명 (복사본) | 크기 | 원본 파일명 |
|---|---|---|
| catalog_v10_8.pdf | 17,175,556 B (16.38 MB) | WOCS_Catalog_v10_8.pdf |

> 원본 위치: (로컬 전용)

## brochure/ (1개)

| 파일명 | 크기 |
|---|---|
| wocs_brochure_v3.pdf | 6,417,430 B (6.12 MB) |

> 원본 위치: (로컬 전용)

## product_brochure/ (16개)

> 원본 위치: (로컬 전용 — 카탈로그·브로셔 아카이브 내 `WOCS_Brochures_Final_64` 묶음)
> 필터: `*_KO_Print.pdf` (KO + Print 모두 포함, Dark/EN 제외)

| 파일명 | 크기 (bytes) |
|---|---|
| WOCS_D-Dome_Brochure_KO_Print.pdf | 811,555 |
| WOCS_D-Pro_Brochure_KO_Print.pdf | 699,450 |
| WOCS_D600_Brochure_KO_Print.pdf | 718,602 |
| WOCS_D800_Brochure_KO_Print.pdf | 695,143 |
| WOCS_EX_Brochure_KO_Print.pdf | 729,637 |
| WOCS_Lodge_Brochure_KO_Print.pdf | 667,484 |
| WOCS_LodgeLX_Brochure_KO_Print.pdf | 609,337 |
| WOCS_S-Classic_Brochure_KO_Print.pdf | 750,833 |
| WOCS_SigA_Brochure_KO_Print.pdf | 606,099 |
| WOCS_SigH_Brochure_KO_Print.pdf | 713,415 |
| WOCS_SigM_Brochure_KO_Print.pdf | 681,293 |
| WOCS_SigO_Brochure_KO_Print.pdf | 696,836 |
| WOCS_SigP_Brochure_KO_Print.pdf | 632,943 |
| WOCS_SigQ_Brochure_KO_Print.pdf | 703,656 |
| WOCS_SigT_Brochure_KO_Print.pdf | 681,282 |
| WOCS_Suite_Brochure_KO_Print.pdf | 637,889 |

## fiti/ (9개, 중복 1개 삭제 후)

> 원본 위치: (로컬 전용 — FITI 시험성적서 보관 폴더)
> 중복 삭제 기록: `DEDUPE_LOG.md`

| 파일명 | 크기 (bytes) | 소재 분류 |
|---|---|---|
| 2025.10.29 STP5052 - 내수도.PDF | 109,669 | STP5052 |
| 2025.10.29 STP5052 FR - 방염성.PDF | 143,462 | STP5052 |
| 2025.10.29 STP5052 - 기본물성.PDF | 145,867 | STP5052 |
| STP1054XCL FR 방염.PDF | 135,072 | STP1054XCL |
| 2025.06.12 STP1060PVDF - 질량,인장,인열,접착,방염.PDF | 157,698 | STP1060PVDF |
| STP1054XCL 아이보리(졸)FR - 인장,인열,접착,방염,질량.PDF | 280,340 | STP1054XCL |
| STP1054X 오렌지(졸)FR - 인장,인열,접착,방염,질량.PDF | 289,038 | STP1054X |
| STP1055(졸) PCF FR 중금속,프탈레이트테스트 (1).pdf | 227,867 | STP1055 |
| pvc글램핑원단 (1).pdf | 3,768,157 | PVC 원단 종합 |

---

## 보안 검증 (2026-04-21)

- ✅ 출원 중 문서 (명세/증명서 등) 포함 파일 없음
- ✅ 견적/증빙 지원서류 (가족관계·중소기업확인서 등) 포함 파일 없음
- ✅ 웹사이트 배포 복사본(`assets/`, `dist/`) 경로에서 복사된 것 없음 — 원본만
- ✅ 이 매니페스트 내 절대 경로·이메일·전화번호·바이어명·가격 정보 **없음** (2026-04-21 redact 완료)

## 알려진 이슈 / 메모

1. ~~**내수도 중복 추정**~~ → **해결 (2026-04-21)**: SHA256 해시 `15bbe21f...` 완전 일치 확인. `내수도-1.PDF` 삭제, `내수도.PDF` 유지. 상세 로그는 `DEDUPE_LOG.md` 참고.
2. **FITI 실제 10종**: 사용자가 처음 제시한 "FITI 5종"과 불일치. 전체 10종 인덱싱할지, 5종으로 축소할지 이후 단계에서 결정 필요.
3. **원본 비이동**: 모든 원본 파일은 로컬의 별도 보관 폴더(저장소 외)에 그대로 유지됨 (복사만 수행).
