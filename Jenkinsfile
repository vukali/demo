pipeline {
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    command: ["/busybox/cat"]
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
    // Repo structure của bạn
    DOCKER_CONTEXT = "."                // repo root
    DOCKERFILE     = "Dockerfile"       // repo root
    K8S_DIR        = "demo-k8s"
    KUSTOM_FILE    = "demo-k8s/kustomization.yaml"

    // Harbor
    HARBOR_HOST    = "harbor.watasoftware.com"
    HARBOR_PROJECT = "demo"
    IMAGE_NAME     = "hello-k8s"
    IMAGE_REPO     = "${HARBOR_HOST}/${HARBOR_PROJECT}/${IMAGE_NAME}"

    // Tag theo commit short SHA
    IMAGE_TAG      = "${env.GIT_COMMIT?.take(7) ?: env.BUILD_NUMBER}"
  }

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  stages {
    stage("Checkout") {
      steps { checkout scm }
    }

    stage("Build & Push to Harbor (Kaniko)") {
      steps {
        container('kaniko') {
          withCredentials([usernamePassword(credentialsId: 'harbor-cred',
                                            usernameVariable: 'HARBOR_USER',
                                            passwordVariable: 'HARBOR_PASS')]) {
            sh '''
              set -eux
              cat > /kaniko/.docker/config.json <<EOF
              { "auths": { "${HARBOR_HOST}": { "username": "${HARBOR_USER}", "password": "${HARBOR_PASS}" } } }
EOF

              echo "Building ${IMAGE_REPO}:${IMAGE_TAG}"
              /kaniko/executor \
                --context "${WORKSPACE}/${DOCKER_CONTEXT}" \
                --dockerfile "${WORKSPACE}/${DOCKERFILE}" \
                --destination "${IMAGE_REPO}:${IMAGE_TAG}"
            '''
          }
        }
      }
    }

    stage("Bump image tag in kustomization.yaml & push Git") {
      steps {
        container('tools') {
          withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
            sh '''
              set -eux
              apk add --no-cache git yq

              git config user.email "jenkins@local"
              git config user.name  "jenkins"

              ORIGIN_URL=$(git remote get-url origin)
              if echo "$ORIGIN_URL" | grep -q "^https://"; then
                git remote set-url origin "https://${GITHUB_TOKEN}@${ORIGIN_URL#https://}"
              fi

              FILE="${KUSTOM_FILE}"

              # đảm bảo có images: []
              if ! yq '.images' "$FILE" >/dev/null 2>&1; then
                yq -i '.images = []' "$FILE"
              fi

              # add/update entry đúng image repo
              if ! yq -e '.images[] | select(.name=="'"${IMAGE_REPO}"'")' "$FILE" >/dev/null 2>&1; then
                yq -i '.images += [{"name":"'"${IMAGE_REPO}"'","newTag":"'"${IMAGE_TAG}"'"}]' "$FILE"
              else
                yq -i '(.images[] | select(.name=="'"${IMAGE_REPO}"'") | .newTag) = "'"${IMAGE_TAG}"'"' "$FILE"
              fi

              git add "$FILE"
              git commit -m "chore(hello-k8s): bump image tag to ${IMAGE_TAG}" || true
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
  }
}
