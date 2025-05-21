pipeline {
    agent any
    
    environment {
        // MCP 서버 설정 및 테스트 환경 변수
        MCP_SERVER_PORT = "5001" // 테스트용 MCP 서버 포트
        MCP_CONFIG_PATH = "${WORKSPACE}/claude_desktop_config.json" // MCP 구성 파일 경로
        REPO_URL = "https://github.com/bgradecoding/ex-mcp.git" // 깃 저장소 URL
        BRANCH_NAME = "main" // 검사할 브랜치
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                // Git 저장소 클론
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${BRANCH_NAME}"]],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [[$class: 'CleanBeforeCheckout']],
                    submoduleCfg: [],
                    userRemoteConfigs: [[url: "${REPO_URL}"]]
                ])
                
                // 클론이 성공적으로 완료되었는지 확인
                sh 'ls -la'
            }
        }
        
        stage('Setup Environment') {
            steps {
                bash '''
                
                # UV 패키지 매니저 설치 (이미 설치되어 있지 않은 경우)
                if ! command -v uv &> /dev/null; then
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    
                    # 설치 경로 확인 및 환경 변수 설정
                    echo 'export PATH="/root/.local/bin:$PATH"' >> ~/.bashrc
                    source ~/.bashrc
                    
                    uv --version || (echo "UV 설치 실패"; exit 1)
                fi
                
                # Python 가상 환경 설정
                uv venv
                
                # 가상 환경 활성화
                source .venv/bin/activate || . .venv/bin/activate
                
                # 프로젝트 의존성 설치
                if [ -f "requirements.txt" ]; then
                    uv pip install -r requirements.txt
                fi
                
                # MCP-Scan 설치
                uv pip install mcp-scan
                
                # 설치 확인
                python -m mcp_scan --version || (echo "MCP-Scan 설치 실패"; exit 1)
                '''
            }
        }
        
        stage('Start MCP Server') {
            steps {
                script {
                    // MCP 서버를 백그라운드로 시작
                    sh '''
                    # 가상 환경 활성화
                    source .venv/bin/activate || . .venv/bin/activate
                    
                    
                    # 테스트용 MCP 서버 시작
                    python sse_server.py &
                    echo $! > mcp_server.pid
                    
                    # 서버가 시작될 때까지 잠시 대기
                    echo "MCP 서버 시작 중..."
                    sleep 10
                    
                    # 서버가 실행 중인지 확인
                    # 건강 상태 엔드포인트가 있는 경우
                    curl -s http://localhost:${MCP_SERVER_PORT}/sse || echo "Health 엔드포인트 없음, 포트 확인으로 대체"
                    
                    # 포트가 열려 있는지 확인
                    nc -z localhost ${MCP_SERVER_PORT} || (echo "서버 시작 실패: 포트 ${MCP_SERVER_PORT}가 열려있지 않음"; exit 1)
                    
                    echo "MCP 서버가 성공적으로 시작되었습니다"
                    '''
                }
            }
        }
        
        stage('Generate MCP Config') {
            steps {
                script {
                    // 테스트용 mcp.json 구성 파일 생성
                    sh '''
                    # 기존 claude_desktop_config.json 파일이 있는지 확인
                    if [ -f "claude_desktop_config.json" ]; then
                        cp claude_desktop_config.json ${MCP_CONFIG_PATH}
                    else
                        # 테스트용 구성 파일 생성
                        cat > ${MCP_CONFIG_PATH} << EOL
{
  "mcpServers": {
    "test_server": {
      "transport": "sse",
      "url": "http://localhost:${MCP_SERVER_PORT}"
    }
  }
}
EOL
                    fi
                    
                    echo "MCP 구성 파일 생성 완료: ${MCP_CONFIG_PATH}"
                    cat ${MCP_CONFIG_PATH}
                    '''
                }
            }
        }
        
        stage('Run MCP-Scan') {
            steps {
                script {
                    // MCP-Scan 실행하여 취약점 검사
                    sh '''
                    # 가상 환경 활성화
                    source .venv/bin/activate || . .venv/bin/activate
                    
                    echo "MCP-Scan 실행 중..."
                    
                    # JSON 형식으로 출력하여 결과 파싱이 쉽도록 함
                    # 자세한 출력을 위해 --verbose 플래그 추가
                    mcp-scan scan --json --verbose ${MCP_CONFIG_PATH} > scan_results.json
                    
                    # 결과 출력
                    echo "MCP-Scan 결과:"
                    cat scan_results.json
                    
                    # 결과 분석 및 실패 조건 확인
                    if grep -q "\"verified\":false" scan_results.json; then
                        echo "취약점이 발견되었습니다. 배포를 중단합니다."
                        exit 1
                    fi
                    
                    echo "MCP-Scan 취약점 검사 완료: 문제가 발견되지 않았습니다."
                    '''
                }
            }
        }
        
        stage('Verify Tool Descriptions') {
            steps {
                script {
                    // 도구 설명 검사를 위한 추가 단계
                    sh '''
                    # 가상 환경 활성화
                    source .venv/bin/activate || . .venv/bin/activate
                    
                    echo "도구 설명 검사 중..."
                    
                    # 도구 설명 검사 (inspect 명령어 사용)
                    mcp-scan inspect ${MCP_CONFIG_PATH} > tool_descriptions.txt
                    
                    # 결과 출력
                    echo "도구 설명 검사 결과:"
                    cat tool_descriptions.txt
                    
                    # 특정 패턴 검사 (예: 민감한 파일 읽기 시도)
                    if grep -i -E '(~/\\.ssh|/\\.env|password|credential|token|<IMPORTANT>)' tool_descriptions.txt; then
                        echo "도구 설명에서 잠재적인 보안 문제가 발견되었습니다."
                        exit 1
                    fi
                    
                    echo "도구 설명 검사 완료: 의심스러운 패턴이 발견되지 않았습니다."
                    '''
                }
            }
        }
        
        stage('Create Security Report') {
            steps {
                script {
                    // 보안 검사 결과를 보고서로 저장
                    sh '''
                    # 가상 환경 활성화
                    source .venv/bin/activate || . .venv/bin/activate
                    
                    echo "보안 보고서 생성 중..."
                    
                    # 보고서 디렉토리 생성
                    mkdir -p security-reports
                    
                    # 결과 파일을 보고서 디렉토리로 복사
                    cp scan_results.json security-reports/
                    cp tool_descriptions.txt security-reports/
                    
                    # 요약 보고서 생성
                    echo "MCP-Scan Security Report - $(date)" > security-reports/summary.txt
                    echo "======================================" >> security-reports/summary.txt
                    echo "" >> security-reports/summary.txt
                    
                    # 도구 수 추출 및 추가
                    TOOL_COUNT=$(grep -c "\"name\":" scan_results.json || echo 0)
                    echo "Total tools scanned: ${TOOL_COUNT}" >> security-reports/summary.txt
                    
                    # 취약점 수 추출 및 추가
                    VULN_COUNT=$(grep -c "\"verified\":false" scan_results.json || echo 0)
                    echo "Vulnerabilities found: ${VULN_COUNT}" >> security-reports/summary.txt
                    
                    echo "보안 보고서 생성 완료"
                    '''
                    
                    // 결과 아티팩트 저장
                    archiveArtifacts artifacts: 'security-reports/**', allowEmptyArchive: true
                }
            }
        }
    }
    
    post {
        success {
            echo "MCP 서버 보안 검사가 성공적으로 완료되었습니다. 배포를 진행합니다."
        }
        failure {
            echo "MCP 서버 보안 검사 중 취약점이 발견되었습니다. 배포가 중단되었습니다."
        }
        always {
            // 항상 정리
            sh '''
            echo "정리 작업 수행 중..."
            
            # MCP 서버 프로세스 종료
            if [ -f mcp_server.pid ]; then
                echo "PID 파일을 사용하여 MCP 서버 종료"
                kill $(cat mcp_server.pid) || true
                rm mcp_server.pid
            fi
            
            # 또는 프로세스 이름으로 종료
            echo "프로세스 이름으로 MCP 서버 종료 시도"
            pkill -f "python.*server\\.py" || true
            
            echo "정리 작업 완료"
            '''
        }
    }
}