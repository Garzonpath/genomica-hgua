import requests

def buscar(gene, variant):
    """Busca en CIVICdb. Ejemplo: buscar("BRAF", "V600E")"""
    
    query = """
    query($gene: String!, $variant: String!) {
      variants(name: $variant, geneName: $gene) {
        nodes {
          name
          link
          molecularProfiles {
            nodes {
              evidenceItems {
                nodes {
                  evidenceLevel
                  significance
                  description
                  therapies { nodes { name } }
                }
              }
            }
          }
        }
      }
    }
    """
    
    try:
        r = requests.post(
            "https://civicdb.org/api/graphql",
            json={"query": query, "variables": {"gene": gene, "variant": variant}},
            timeout=10
        )
        
        data = r.json()
        variants = data.get("data", {}).get("variants", {}).get("nodes", [])
        
        if not variants:
            return None
        
        v = variants[0]
        profiles = v.get("molecularProfiles", {}).get("nodes", [])
        
        evidencias = []
        terapias = set()
        
        for p in profiles:
            for ev in p.get("evidenceItems", {}).get("nodes", []):
                evidencias.append({
                    'nivel': ev.get('evidenceLevel', ''),
                    'significancia': ev.get('significance', ''),
                    'descripcion': ev.get('description', '')[:100]
                })
                for t in ev.get('therapies', {}).get('nodes', []):
                    terapias.add(t.get('name', ''))
        
        return {
            'url': f"https://civicdb.org{v.get('link', '')}",
            'evidencias': evidencias[:5],
            'terapias': list(terapias)
        }
    except:
        return None
