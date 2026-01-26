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
    DOCKER_CONTEXT = "."
    DOCKERFILE     = "Dockerfile"

    KUSTOM_FILE    = "demo-k8s/kustomization.yaml"

    HARBOR_HOST    = "harbor.watasoftware.com"
    HARBOR_PROJECT = "demo"
    IMAGE_NAME     = "hello-k8s"
    IMAGE_REPO     = "${HARBOR_HOST}/${HARBOR_PROJECT}/${IMAGE_NAME}"
  }

  options {
    disableConcurrentBuilds()
    // BỎ timestamps() vì Jenkins bạn không support option này
  }

  stages {
    stage("Checkout") {
      steps { checkout scm }
    }

    stage("Set Image Tag") {
      steps {
        script {
          env.IMAGE_TAG = (env.GIT_COMMIT?.take(7) ?: env.BUILD_NUMBER)
          echo "IMAGE_TAG=${env.IMAGE_TAG}"
        }
      }
    }

    stage("Build & Push to Harbor (Kaniko)") {
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

              echo "Building ${IMAGE_REPO}:${IMAGE_TAG} and :latest"
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

    stage("Bump kustomize tag & push Git (for ArgoCD)") {
      steps {
        container('tools') {
          withCredentials([usernamePassword(credentialsId: 'github-pat',
                                            usernameVariable: 'GH_USER',
                                            passwordVariable: 'GH_TOKEN')]) {
            sh '''
              set -eu
              apk add --no-cache git yq

              git config user.email "jenkins@local"
              git config user.name  "jenkins"

              # Jenkins checkout thường ở detached HEAD -> đảm bảo có branch main local để commit
              git fetch origin main
              git checkout -B main origin/main

              FILE="${KUSTOM_FILE}"

              # đảm bảo có images array
              if ! yq '.images' "$FILE" >/dev/null 2>&1; then
                yq -i '.images = []' "$FILE"
              fi

              # update đúng image repo
              if ! yq -e '.images[] | select(.name=="'"${IMAGE_REPO}"'")' "$FILE" >/dev/null 2>&1; then
                yq -i '.images += [{"name":"'"${IMAGE_REPO}"'","newTag":"'"${IMAGE_TAG}"'"}]' "$FILE"
              else
                yq -i '(.images[] | select(.name=="'"${IMAGE_REPO}"'") | .newTag) = "'"${IMAGE_TAG}"'"' "$FILE"
              fi

              git add "$FILE"
              git commit -m "chore(hello-k8s): bump image tag to ${IMAGE_TAG} [skip jenkins]" || true

              # push dùng PAT: format https://user:token@...
              git push "https://${GH_USER}:${GH_TOKEN}@github.com/vukali/demo.git" HEAD:main
            '''
          }
        }
      }
    }
  }

  post {
    success {
      echo "DONE: pushed ${IMAGE_REPO}:${IMAGE_TAG} + updated ${KUSTOM_FILE}. ArgoCD autosync sẽ rollout."
    }
  }
}