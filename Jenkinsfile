pipeline {
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command: ["/busybox","cat"]
    tty: true
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  - name: tools
    image: alpine:3.20
    command: ["/bin/sh","-c","cat"]
    tty: true
  volumes:
  - name: docker-config
    emptyDir: {}
"""
    }
  }

  environment {
    DOCKER_CONTEXT = "."
    DOCKERFILE     = "Dockerfile"
    KUSTOM_FILE    = "demo-k8s/kustomization.yaml"

    HARBOR_HOST    = "harbor.watasoftware.com"
    HARBOR_PROJECT = "demo"
    IMAGE_NAME     = "hello-k8s"
    IMAGE_REPO     = "${HARBOR_HOST}/${HARBOR_PROJECT}/${IMAGE_NAME}"

    // marker để tránh loop
    SKIP_MARKER    = "[skip-jenkins]"
    BOT_EMAIL      = "jenkins@local"
    SKIP_BUILD     = "false"
  }

  options { disableConcurrentBuilds() }

  stages {
    stage("Checkout") {
      steps { checkout scm }
    }

    stage("Anti-loop (skip bot commit)") {
      steps {
        container('tools') {
          script {
            sh 'apk add --no-cache git >/dev/null'

            def authorEmail = sh(returnStdout: true, script: 'git log -1 --pretty=format:%ae || true').trim()
            def msg         = sh(returnStdout: true, script: 'git log -1 --pretty=format:%s  || true').trim()

            echo "Last commit author: ${authorEmail}"
            echo "Last commit msg   : ${msg}"

            if (authorEmail == env.BOT_EMAIL || msg.contains(env.SKIP_MARKER)) {
              env.SKIP_BUILD = "true"
              echo "Skip build: detected bot commit or ${env.SKIP_MARKER}"
            }
          }
        }
      }
    }

    stage("Set Image Tag") {
      when { expression { return env.SKIP_BUILD != "true" } }
      steps {
        script {
          def sha = env.GIT_COMMIT ?: ""
          env.IMAGE_TAG = (sha.length() >= 7) ? sha.substring(0,7) : env.BUILD_NUMBER
          echo "IMAGE_TAG=${env.IMAGE_TAG}"
        }
      }
    }

    stage("Build & Push to Harbor (Kaniko)") {
      when { expression { return env.SKIP_BUILD != "true" } }
      steps {
        container('kaniko') {
          withCredentials([usernamePassword(credentialsId: 'harbor-cred',
                                            usernameVariable: 'HARBOR_USER',
                                            passwordVariable: 'HARBOR_PASS')]) {
            sh '''
              set -eu
              cat > /kaniko/.docker/config.json <<EOF
              { "auths": { "${HARBOR_HOST}": { "username": "${HARBOR_USER}", "password": "${HARBOR_PASS}" } } }
EOF
              /kaniko/executor \
                --context "${WORKSPACE}/${DOCKER_CONTEXT}" \
                --dockerfile "${WORKSPACE}/${DOCKERFILE}" \
                --destination "${IMAGE_REPO}:${IMAGE_TAG}" \
                --destination "${IMAGE_REPO}:latest"
            '''
          }
        }
      }
    }

    stage("Bump image tag in kustomization.yaml & push Git") {
      when { expression { return env.SKIP_BUILD != "true" } }
      steps {
        container('tools') {
          withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
            sh '''
              set -eu
              apk add --no-cache git yq >/dev/null

              git config user.email "${BOT_EMAIL}"
              git config user.name  "jenkins"

              ORIGIN_URL=$(git remote get-url origin)
              case "$ORIGIN_URL" in
                https://*)
                  # dùng x-access-token để auth ổn định
                  git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@${ORIGIN_URL#https://}"
                  ;;
              esac

              FILE="${KUSTOM_FILE}"

              # ensure .images exists
              if ! yq '.images' "$FILE" >/dev/null 2>&1; then
                yq -i '.images = []' "$FILE"
              fi

              # add/update images entry
              if ! yq -e '.images[] | select(.name=="'"${IMAGE_REPO}"'")' "$FILE" >/dev/null 2>&1; then
                yq -i '.images += [{"name":"'"${IMAGE_REPO}"'","newTag":"'"${IMAGE_TAG}"'"}]' "$FILE"
              else
                yq -i '(.images[] | select(.name=="'"${IMAGE_REPO}"'") | .newTag) = "'"${IMAGE_TAG}"'"' "$FILE"
              fi

              git add "$FILE"
              git commit -m "chore(hello-k8s): bump image tag to ${IMAGE_TAG} ${SKIP_MARKER}" || true
              git push origin HEAD:main
            '''
          }
        }
      }
    }
  }

  post {
    success {
      echo "OK: pushed ${IMAGE_REPO}:${IMAGE_TAG} + updated ${KUSTOM_FILE}. ArgoCD autosync sẽ rollout."
    }
    always {
      script {
        if (env.SKIP_BUILD == "true") {
          echo "Build was skipped by anti-loop logic."
        }
      }
    }
  }
}
