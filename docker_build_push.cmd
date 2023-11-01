cd frontend
call npm run build -- --mode msk-dormakaba
cd ..
docker build . -t terminal9160-async
docker tag terminal9160-async kuznetsovsergey/9160:v1
docker push kuznetsovsergey/9160:v1