.PHONY: train docker k8s

train:
	python ml/training/train.py --data /data/FaceForensics++

docker:
	docker-compose up --build

k8s:
	kubectl apply -f deployment/k8s/

mlflow:
	mlflow ui --port 5000
