pipeline {
    agent any
    stages {
        stage ('Checkout') {
            steps{
                checkout scm
            }
        }
        stage ('docker build') {
            steps {
                docker build -t peeps:latest -f deployment/nginx/Dockerfile .
            }
        }
        
    }
}