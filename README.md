# TP3 ShopAlto — Kit professeur, Windows 11 / Docker Desktop

## Lancer
Dans VS Code PowerShell, dans ce dossier :

```powershell
docker compose config
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://localhost:8080/catalog
Invoke-RestMethod http://localhost:8080/ready
Invoke-RestMethod -Method Post -Uri http://localhost:8080/orders -ContentType 'application/json' -Body '{"product_id":1,"quantity":2}'
Invoke-RestMethod http://localhost:8080/orders/count
```

## Interfaces
- ShopAlto http://localhost:8080
- HAProxy http://localhost:8404/stats
- Prometheus http://localhost:9090/targets
- Alertmanager http://localhost:9093
- Grafana http://localhost:3000 (admin / tp3-local-only)
- cAdvisor http://localhost:8085 (selon compatibilité Docker Desktop)

## Tests de résilience
```powershell
# Éteindre web1 volontairement : il NE redémarre pas immédiatement malgré restart:unless-stopped
docker compose stop web1
1..10 | ForEach-Object { (Invoke-RestMethod http://localhost:8080/catalog | ConvertTo-Json -Compress); Start-Sleep -Seconds 1 }
# Relever la panne de web1 et l'alerte WebNodeDown (attendre >20s)
docker compose start web1

# Arrêter tous les frontaux : HTTP 503 attendu
# Pour voir le code HTTP :
curl.exe -i http://localhost:8080/catalog
docker compose stop web1 web2
curl.exe -i http://localhost:8080/catalog
docker compose start web1 web2

# Panne PostgreSQL : /ready et /catalog doivent échouer
docker compose stop postgres
curl.exe -i http://localhost:8080/ready
curl.exe -i http://localhost:8080/catalog
docker compose start postgres
```

## Persistance PostgreSQL
```powershell
docker compose exec postgres psql -U shopalto -d shopalto -c 'SELECT id,product_id,quantity,total FROM orders ORDER BY id;'
docker compose restart postgres
docker compose exec postgres psql -U shopalto -d shopalto -c 'SELECT COUNT(*) FROM orders;'
```

## Sauvegarde / restauration (à tester sur environnement de laboratoire)
```powershell
# Génère un SQL brut dans le fichier backup_shopalto.sql de votre machine
docker compose exec -T postgres pg_dump -U shopalto -d shopalto --clean --if-exists > backup_shopalto.sql
# Ne jamais restaurer automatiquement dans la base de production.
```

## Tests de charge facultatifs (conteneur k6, sans installation locale)
```powershell
docker run --rm --network shopalto-tp3_default -v "${PWD}/loadtest:/scripts:ro" grafana/k6:0.55.0 run /scripts/load.js
```

## Vérification de la supervision
- Dans Prometheus, vérifier `up`, `probe_success`, `pg_up`.
- Dans Grafana, Explore > Prometheus, afficher `probe_success`.
- Alertmanager enregistre les alertes actives, mais **la configuration fournie ne transmet pas de courriel** : il faut ajouter un récepteur réel pour tester une notification.
- cAdvisor peut fonctionner de façon incomplète sur Docker Desktop Windows/WSL2; ce n'est pas une preuve que le service applicatif est indisponible.

## Limites pédagogiques
- HAProxy, les deux Nginx, l'API et PostgreSQL sont sur le même hôte Docker : pas de haute disponibilité en cas de panne de l'hôte.
- Un seul API et un seul PostgreSQL restent des SPOF.
- Les URLs /health des Nginx prouvent uniquement la disponibilité locale des Nginx, tandis que /ready et /catalog testent l'accès à l'API et à la base.
- Les commandes `docker compose stop` sont des arrêts administratifs volontaires; `restart: unless-stopped` ne constitue pas de l'auto-healing fonctionnel.
- Ce dossier est strictement local : mots de passe de laboratoire et endpoints non sécurisés.
- Pour un vrai PRA, ajouter sauvegardes externes, objectifs RTO/RPO, tests de restauration et infrastructure répartie sur plusieurs hôtes.
