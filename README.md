# steam-games-database  
database was taken from kaggle:  
https://www.kaggle.com/datasets/antonkozyriev/game-recommendations-on-steam  

EER Diagramm:  
<img width="1130" height="922" alt="image" src="https://github.com/user-attachments/assets/01367e6c-87a2-42d7-968d-b28d36ac7381" />  
  
Instalation:  
git clone https://github.com/yourname/steam-sql-queries.git  
cd steam-sql-queries  
python -m venv venv  
source venv/bin/activate      # Linux / Mac  
venv\Scripts\activate         # Windows  
pip install mysql-connector-python tabulate  
CREATE DATABASE games;  
mysql -u root -p games < dump.sql  

Connect to database using mysql shell:  
\sql  
\connect root@localhost:3306  
show databases;  
use valorant_stats;  

  
Start:  
python main.py  
