● Hier ist die komplette Food API Dokumentation:

  Food API Endpunkte

  | Endpunkt                                    | Methode | Beschreibung                 |
  | ------------------------------------------- | ------- | ---------------------------- |
  | /api/food/search?q=milch                    | GET     | Suche nach Produkten         |
  | /api/food/search?store=Lidl                 | GET     | Produkte eines Stores        |
  | /api/food/search?q=joghurt&store=Lidl       | GET     | Suche in Store               |
  | /api/food/product/{barcode}                 | GET     | Produkt per Barcode          |
  | /api/food/store/Lidl                        | GET     | Alle Lidl-Produkte           |
  | /api/food/store/Aldi-sud?category=dairy     | GET     | Nach Kategorie filtern       |
  | /api/food/categories                        | GET     | Alle Kategorien + Produkte   |
  | /api/food/categories?category=Milchprodukte | GET     | Produkte einer Kategorie     |
  | /api/food/favorites                         | GET     | Alle Favoriten               |
  | /api/food/favorites                         | POST    | Favorit hinzufügen/entfernen |

  ---
  Externer Zugriff mit Basic Auth (Traefik)

  Dein docker-compose nutzt Traefik mit user-auth@file Middleware. Die Auth-Credentials sind in deiner Traefik-Konfiguration definiert.

  Beispiele mit curl:

  # Basic Auth Credentials (aus deiner Traefik config)
  AUTH="username:password"

  # Produkte suchen
  curl -u "$AUTH" "https://kanban.niclasedge.com/api/food/search?q=milch"

  # Barcode abrufen
  curl -u "$AUTH" "https://kanban.niclasedge.com/api/food/product/4000521003692"

  # Lidl-Produkte (Top 100 nach Yuka Score)
  curl -u "$AUTH" "https://kanban.niclasedge.com/api/food/store/Lidl?limit=100"

  # Aldi-Produkte nach Kategorie
  curl -u "$AUTH" "https://kanban.niclasedge.com/api/food/store/Aldi-sud?category=dairy&sort=score"

  # Favorit hinzufügen
  curl -u "$AUTH" -X POST \
    -H "Content-Type: application/json" \
    -d '{"barcode":"4000521003692","action":"add"}' \
    "https://kanban.niclasedge.com/api/food/favorites"

  Query Parameter für /api/food/store/{store}:

  | Parameter | Werte                                                                   | Default |
  | --------- | ----------------------------------------------------------------------- | ------- |
  | category  | dairy, bread, meat, beverages, snacks, frozen, pasta, breakfast, fruits | all     |
  | sort      | score, name, updated                                                    | score   |
  | limit     | 1-500                                                                   | 500     |
  | offset    | 0+                                                                      | 0       |

  Stores:

  - Lidl
  - Aldi-sud