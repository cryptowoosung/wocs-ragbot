#!/usr/bin/env bash
# WOCS RAG Bot - GitHub 트래픽 모니터링 (Bash / Git Bash)
#
# 사용법:
#   bash scripts/monitor.sh
#
# 기능:
#   - 최근 14일 views / clones + popular paths + referrers
#   - 일 $THRESHOLD 이상 HIGH, 전일 대비 $SPIKE_RATIO 배 이상 SPIKE
#   - logs/monitor_history.json 에 누적 저장
#
# 의존: gh, jq

set -eo pipefail

REPO="${REPO:-cryptowoosung/wocs-ragbot}"
THRESHOLD="${THRESHOLD:-100}"
SPIKE_RATIO="${SPIKE_RATIO:-5}"
HIST_FILE="logs/monitor_history.json"

# ANSI 컬러
C_R=$'\033[31m'
C_Y=$'\033[33m'
C_G=$'\033[32m'
C_C=$'\033[36m'
C_0=$'\033[0m'

# --- 전제 조건 --------------------------------------------------------

if ! command -v gh >/dev/null 2>&1; then
    echo "${C_R}[오류] gh (GitHub CLI) 설치되지 않음.${C_0}" >&2
    echo "       https://cli.github.com/ 에서 설치 후 재시도." >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "${C_R}[오류] jq 설치되지 않음.${C_0}" >&2
    echo "       Windows 설치: choco install jq  또는  winget install jqlang.jq" >&2
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "${C_R}[오류] gh 인증되지 않음. 실행: gh auth login${C_0}" >&2
    exit 1
fi

# --- 헤더 -------------------------------------------------------------

echo "${C_C}== WOCS RAG Bot GitHub 트래픽 모니터 ==${C_0}"
echo "Repo      : $REPO"
echo "임계치    : 일 ${THRESHOLD}회 이상 → HIGH  |  전일 대비 x${SPIKE_RATIO} 이상 → SPIKE"
echo "시작 시각 : $(date '+%Y-%m-%d %H:%M')"
printf '%0.s-' {1..68}; echo

# --- API 호출 헬퍼 ----------------------------------------------------

fetch() {
    gh api "repos/$REPO/$1" 2>/dev/null
}

# --- daily 출력 -------------------------------------------------------
# $1 = kind (views|clones), $2 = array key name
show_daily() {
    local kind="$1"
    local key="$2"
    local json
    json=$(fetch "traffic/$kind") || true
    if [ -z "$json" ]; then
        echo "${C_R}[오류] $kind 조회 실패${C_0}"
        echo "null"
        return
    fi

    echo ""
    echo "${C_Y}-- $kind --${C_0}"
    local total uniq
    total=$(echo "$json" | jq -r '.count')
    uniq=$(echo "$json" | jq -r '.uniques')
    printf "  총계 : %6s    고유 : %6s\n" "$total" "$uniq"

    local count
    count=$(echo "$json" | jq ".${key} | length")
    if [ "$count" -eq 0 ]; then
        echo "  (14일 창 내 일별 데이터 없음)"
        printf "%s" "$json" > /tmp/monitor_${kind}.json
        return
    fi

    echo ""
    printf "  %-12s %8s %8s   %s\n" "날짜" "count" "uniques" "플래그"

    local warn_day=$(( THRESHOLD / 2 )); [ "$warn_day" -lt 1 ] && warn_day=1
    local prev=-1

    while IFS=$'\t' read -r ts c u; do
        local date="${ts%%T*}"
        local flag=""
        local clr=""

        if [ "$c" -ge "$THRESHOLD" ]; then
            flag="!! HIGH (>= $THRESHOLD)"; clr="$C_R"
        elif [ "$c" -ge "$warn_day" ]; then
            flag=".. watch"; clr="$C_Y"
        fi

        # 급증 체크
        if [ "$prev" -ge 1 ]; then
            local threshold_spike=$(( prev * SPIKE_RATIO ))
            if [ "$c" -ge "$threshold_spike" ]; then
                flag=$(printf "!! SPIKE (%d -> %d, x%.1f)" "$prev" "$c" "$(echo "scale=2; $c / $prev" | bc -l)")
                clr="$C_R"
            fi
        fi

        printf "  %-12s %8s %8s   ${clr}%s${C_0}\n" "$date" "$c" "$u" "$flag"
        prev="$c"
    done < <(echo "$json" | jq -r ".${key}[] | [.timestamp, .count, .uniques] | @tsv")

    # 히스토리 용으로 저장
    printf "%s" "$json" > /tmp/monitor_${kind}.json
}

# --- popular 리스트 ---------------------------------------------------
show_top() {
    local path="$1"
    local title="$2"
    local out_name="$3"
    local json
    json=$(fetch "traffic/$path") || true
    if [ -z "$json" ]; then
        echo "${C_R}[오류] $title 조회 실패${C_0}"
        return
    fi

    echo ""
    echo "${C_Y}-- $title --${C_0}"

    local n
    n=$(echo "$json" | jq 'length')
    if [ "$n" -eq 0 ]; then
        echo "  (데이터 없음 — 아직 방문이 적습니다)"
        printf "%s" "$json" > /tmp/monitor_${out_name}.json
        return
    fi

    printf "  %6s %6s  %s\n" "count" "uniq" "이름"
    echo "$json" | jq -r '.[] | [.count, .uniques, (.path // .referrer)] | @tsv' | head -10 | while IFS=$'\t' read -r c u name; do
        printf "  %6s %6s  %s\n" "$c" "$u" "$name"
    done

    printf "%s" "$json" > /tmp/monitor_${out_name}.json
}

# --- 실행 -------------------------------------------------------------

mkdir -p logs

show_daily "views" "views"
show_daily "clones" "clones"
show_top "popular/paths" "인기 경로 (paths)" "paths"
show_top "popular/referrers" "리퍼러 (referrers)" "referrers"

# --- 히스토리 누적 ----------------------------------------------------

NOW_ISO=$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')

ENTRY=$(jq -n \
    --arg ts "$NOW_ISO" \
    --argjson v "$(cat /tmp/monitor_views.json 2>/dev/null || echo null)" \
    --argjson c "$(cat /tmp/monitor_clones.json 2>/dev/null || echo null)" \
    --argjson r "$(cat /tmp/monitor_referrers.json 2>/dev/null || echo null)" \
    --argjson p "$(cat /tmp/monitor_paths.json 2>/dev/null || echo null)" \
    '{timestamp: $ts, views: $v, clones: $c, referrers: $r, paths: $p}')

if [ -f "$HIST_FILE" ]; then
    # 기존이 배열이면 append, 단일 객체면 배열로 감쌈
    if jq -e 'type == "array"' "$HIST_FILE" >/dev/null 2>&1; then
        jq ". + [$ENTRY]" "$HIST_FILE" > /tmp/monitor_hist.json
    else
        jq -s --argjson new "$ENTRY" '. + [$new]' "$HIST_FILE" > /tmp/monitor_hist.json
    fi
    mv /tmp/monitor_hist.json "$HIST_FILE"
else
    echo "[$ENTRY]" > "$HIST_FILE"
fi

COUNT=$(jq 'length' "$HIST_FILE")

# --- 푸터 -------------------------------------------------------------

echo ""
printf '%0.s-' {1..68}; echo
echo "${C_G}완료 : $(date '+%Y-%m-%d %H:%M')  |  히스토리 엔트리 ${COUNT}개 -> $HIST_FILE${C_0}"

# 임시 파일 정리
rm -f /tmp/monitor_views.json /tmp/monitor_clones.json /tmp/monitor_paths.json /tmp/monitor_referrers.json
