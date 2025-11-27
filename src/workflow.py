import json
from urllib import request
import http.server
import socketserver
import copy

WORKFLOW ={
  "3": {
    "inputs": {
      "seed": 460903848048608,
      "steps": 35,
      "cfg": 5,
      "sampler_name": "dpmpp_2m_sde",
      "scheduler": "karras",
      "denoise": 1,
      "model": [
        "4",
        0
      ],
      "positive": [
        "6",
        0
      ],
      "negative": [
        "7",
        0
      ],
      "latent_image": [
        "5",
        0
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "4": {
    "inputs": {
      "ckpt_name": "juggernautXL_ragnarokBy.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Load Checkpoint"
    }
  },
  "5": {
    "inputs": {
      "width": 896,
      "height": 1152,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage",
    "_meta": {
      "title": "Empty Latent Image"
    }
  },
  "6": {
    "inputs": {
      "text": "positive prompt",
      "clip": [
        "4",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "7": {
    "inputs": {
      "text": "nsfw",
      "clip": [
        "4",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "3",
        0
      ],
      "vae": [
        "4",
        2
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "10": {
    "inputs": {
      "guide_size": 512,
      "guide_size_for": True,
      "max_size": 1024,
      "seed": 80075447679254,
      "steps": 10,
      "cfg": 4,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 0.5,
      "feather": 5,
      "noise_mask": True,
      "force_inpaint": True,
      "bbox_threshold": 0.5,
      "bbox_dilation": 10,
      "bbox_crop_factor": 3,
      "sam_detection_hint": "center-1",
      "sam_dilation": 0,
      "sam_threshold": 0.93,
      "sam_bbox_expansion": 0,
      "sam_mask_hint_threshold": 0.7,
      "sam_mask_hint_use_negative": "False",
      "drop_size": 10,
      "wildcard": "",
      "cycle": 1,
      "inpaint_model": False,
      "noise_mask_feather": 20,
      "tiled_encode": False,
      "tiled_decode": False,
      "image": [
        "8",
        0
      ],
      "model": [
        "4",
        0
      ],
      "clip": [
        "4",
        1
      ],
      "vae": [
        "4",
        2
      ],
      "positive": [
        "11",
        0
      ],
      "negative": [
        "12",
        0
      ],
      "bbox_detector": [
        "13",
        0
      ]
    },
    "class_type": "FaceDetailer",
    "_meta": {
      "title": "FaceDetailer"
    }
  },
  "11": {
    "inputs": {
      "text": "",
      "clip": [
        "4",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "12": {
    "inputs": {
      "text": "",
      "clip": [
        "4",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "13": {
    "inputs": {
      "model_name": "bbox/face_yolov8m.pt"
    },
    "class_type": "UltralyticsDetectorProvider",
    "_meta": {
      "title": "UltralyticsDetectorProvider"
    }
  },
  "15": {
    "inputs": {
      "images": [
        "31",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
  "23": {
    "inputs": {
      "model_name": "4x_NMKD-Siax_200k.pth"
    },
    "class_type": "UpscaleModelLoader",
    "_meta": {
      "title": "Load Upscale Model"
    }
  },
  "31": {
    "inputs": {
      "upscale_model": [
        "23",
        0
      ],
      "image": [
        "10",
        0
      ]
    },
    "class_type": "ImageUpscaleWithModel",
    "_meta": {
      "title": "Upscale Image (using Model)"
    }
  }
}




def generate_prompt(data):
    print(f"\n=== DEBUG: Generating prompt ===")
    print(f"Race: {data.get('race', 'dwarf')}, Sex: {data.get('sex', 1)}")
    
    # Base prompt
    parts = [
        "ultra photo-realistic", "realistic full body portrait", "unretouched",
        "portrait", "black background"
    ]
    
    # Race/Sex
    race = data.get('race', 'dwarf').lower()
    sex = "male" if data.get('sex', 1) == 1 else "female"
    parts.append(f"{sex} {race}")
    
    # Add race-specific physical traits
    if race == 'dwarf':
        parts.extend(["short", "stock build", "chubby"])
        print("Added dwarf-specific traits: short, stock build, chubby")
    elif race == 'elf':
        parts.extend(["tall", "slender", "graceful"])
        print("Added elf-specific traits: tall, slender, graceful")
    elif race == 'human':
        parts.append("average build")
        print("Added human-specific trait: average build")
    
    # Tissue styles (hair, beard, etc) - deduplicate
    seen_tissues = {}
    if 'tissue_styles' in data:
        print(f"Processing {len(data['tissue_styles'])} tissue styles...")
        for tissue in data['tissue_styles']:
            desc = tissue.get('length_description', '').strip()
            style = tissue.get('style', '').strip()
            name = tissue.get('tissue', '').strip()
            
            # Skip if any field is empty
            if not desc or not name:
                print(f"  SKIP - empty tissue: desc='{desc}', name='{name}'")
                continue
            
            # Skip clean-shaven entries - they're contradictory with actual hair/beard
            if 'clean-shaven' in desc.lower() or 'clean shaven' in desc.lower():
                print(f"  SKIP - clean-shaven tissue: {desc} {name}")
                continue
                
            # Use tissue name as key to avoid duplicates
            tissue_key = name.lower()
            
            # Build description
            tissue_desc = f"{desc} {style} {name}".strip() if style else f"{desc} {name}"
            
            # Keep only the first occurrence or longest description
            if tissue_key not in seen_tissues:
                seen_tissues[tissue_key] = tissue_desc
                print(f"  ADD tissue: {tissue_desc}")
            elif len(tissue_desc) > len(seen_tissues[tissue_key]):
                print(f"  REPLACE tissue '{seen_tissues[tissue_key]}' with longer: {tissue_desc}")
                seen_tissues[tissue_key] = tissue_desc
            else:
                print(f"  SKIP duplicate tissue: {tissue_desc}")
    
    parts.extend(seen_tissues.values())

    # Body modifiers - deduplicate and filter
    seen_body_mods = set()
    if 'body_modifiers' in data:
        print(f"Processing {len(data['body_modifiers'])} body modifiers...")
        for mod in data['body_modifiers']:
            desc = mod.get('description', '').strip()
            name = mod.get('name', '').strip()
            
            if not desc or not name:
                print(f"  SKIP - empty body mod: desc='{desc}', name='{name}'")
                continue
                
            mod_text = f"{desc} {name}"
            mod_key = name.lower()
            
            if mod_key not in seen_body_mods:
                seen_body_mods.add(mod_key)
                parts.append(mod_text)
                print(f"  ADD body mod: {mod_text}")
            else:
                print(f"  SKIP duplicate body mod: {mod_text}")

    # BP modifiers - deduplicate and filter
    seen_bp_mods = {}
    if 'bp_modifiers' in data:
        print(f"Processing {len(data['bp_modifiers'])} BP modifiers...")
        for mod in data['bp_modifiers']:
            desc = mod.get('description', '').strip()
            name = mod.get('name', '').strip()
            
            if not desc or not name:
                print(f"  SKIP - empty BP mod: desc='{desc}', name='{name}'")
                continue
            
            if desc == 'average':
                print(f"  SKIP - average BP mod: {name}")
                continue
                
            bp_key = name.lower()
            
            # Keep only non-average descriptions
            mod_text = f"{desc} {name}"
            if bp_key not in seen_bp_mods:
                seen_bp_mods[bp_key] = mod_text
                print(f"  ADD BP mod: {mod_text}")
            else:
                print(f"  SKIP duplicate BP mod: {mod_text}")
    
    parts.extend(seen_bp_mods.values())

    # Colors - deduplicate
    seen_colors = {}
    if 'color_modifiers' in data:
        print(f"Processing {len(data['color_modifiers'])} color modifiers...")
        for color in data['color_modifiers']:
            c = color.get('color', '').strip()
            p = color.get('part', '').strip()
            
            if not c or not p:
                print(f"  SKIP - empty color: color='{c}', part='{p}'")
                continue
                
            # Normalize color names (e.g., "iris_eye_pine_green" -> "pine green")
            original_c = c
            c = c.replace('_', ' ').replace('iris eye ', '').replace('colored', '').strip()
            
            color_key = p.lower()
            if color_key not in seen_colors:
                seen_colors[color_key] = f"{c} {p}"
                print(f"  ADD color: {c} {p} (from '{original_c}')")
            else:
                print(f"  SKIP duplicate color for {p}")
    
    parts.extend(seen_colors.values())

    # Equipment - limit to most important visible items
    if 'equipment' in data:
        worn = data['equipment'].get('worn', [])
        if worn:
            print(f"Processing {len(worn)} equipment items...")
            # Prioritize visible armor/clothing - separate by category
            helms = []
            torso_items = []
            leg_items = []
            other_items = []
            
            for item in worn:
                item_lower = item.lower()
                if 'helm' in item_lower or 'cap' in item_lower or 'hat' in item_lower:
                    helms.append(item)
                    print(f"  HELM: {item}")
                elif any(keyword in item_lower for keyword in ['shirt', 'tunic', 'armor', 'dress', 'cloak', 'robe']):
                    torso_items.append(item)
                    print(f"  TORSO: {item}")
                elif 'leggings' in item_lower or 'greaves' in item_lower or 'skirt' in item_lower:
                    leg_items.append(item)
                    print(f"  LEGS: {item}")
                elif 'quiver' not in item_lower and 'sock' not in item_lower and 'glove' not in item_lower and 'gauntlet' not in item_lower:
                    other_items.append(item)
                    print(f"  OTHER: {item}")
                else:
                    print(f"  SKIP: {item}")
            
            print(f"Helms: {len(helms)}, Torso: {len(torso_items)}, Legs: {len(leg_items)}, Other: {len(other_items)}")
            
            # Build final list: helm first (most important), then best torso/legs
            visible_items = []
            if helms:
                visible_items.append(helms[0])  # Take first helm
            if torso_items:
                visible_items.append(torso_items[-1])  # Take last/outermost torso item
            if leg_items:
                visible_items.append(leg_items[0])  # Take first legs item
            
            # Fill remaining slots up to 4 total items
            remaining_slots = 4 - len(visible_items)
            if remaining_slots > 0 and other_items:
                visible_items.extend(other_items[:remaining_slots])
            
            print(f"Selected {len(visible_items)} items: {visible_items}")
            
            if visible_items:
                # Simplify material names and clean up descriptions
                simplified_items = []
                for item in visible_items:
                    # Remove size prefixes (large, small, etc.)
                    simplified = item
                    for size in ['large ', 'small ', 'medium ', 'giant ', 'enormous ', 'gigantic ']:
                        simplified = simplified.replace(size, '')
                    
                    # Simplify common material compounds
                    material_simplifications = {
                        'bismuth bronze': 'bronze',
                        'pig tail': 'cloth',
                        'rope reed': 'cloth',
                        'cave spider silk': 'silk',
                        'giant cave spider silk': 'silk',
                        'chain leggings': 'chainmail leggings',
                        'mail shirt': 'chainmail',
                        # Simplify all animal materials
                        'pig leather': 'leather',
                        'vulture leather': 'leather',
                        'octopus leather': 'leather',
                        'grizzly bear leather': 'leather',
                        'donkey leather': 'leather',
                        'sheep wool': 'wool',
                        'llama wool': 'wool',
                        'white stork leather': 'leather',
                        'chicken leather': 'leather',
                        'turkey leather': 'leather',
                        'basking shark leather': 'leather',
                        'sheep leather': 'leather',
                    }
                    
                    for original, replacement in material_simplifications.items():
                        simplified = simplified.replace(original, replacement)
                    
                    # Remove dyed information (clutters prompt)
                    if '(dyed' in simplified:
                        simplified = simplified.split('(dyed')[0].strip()
                    
                    # Remove redundant words after simplification
                    simplified = simplified.replace('leather leather', 'leather')
                    simplified = simplified.replace('cloth cloth', 'cloth')
                    simplified = simplified.replace('chainmail chainmail', 'chainmail')
                    
                    # Clean up extra spaces
                    simplified = ' '.join(simplified.split())
                    
                    simplified_items.append(simplified)
                    if simplified != item:
                        print(f"  SIMPLIFIED: '{item}' -> '{simplified}'")
                
                items = ", ".join(simplified_items)
                parts.append(f"wearing {items}")
                print(f"Final equipment list ({len(simplified_items)} items): {items}")
            
    # Suffix
    parts.extend([
        "full body visible", "studio lighting", "high detail", "8k", "professional photography"
    ])
    
    final_prompt = ", ".join(parts)
    print(f"\n=== FINAL PROMPT ({len(final_prompt)} chars) ===")
    print(final_prompt)
    print("=" * 50 + "\n")
    
    return final_prompt

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}

    # If the workflow contains API nodes, you can add a Comfy API key to the `extra_data`` field of the payload.
    # p["extra_data"] = {
    #     "api_key_comfy_org": "comfyui-87d01e28d*******************************************************"  # replace with real key
    # }
    # See: https://docs.comfy.org/tutorials/api-nodes/overview
    # Generate a key here: https://platform.comfy.org/login

    data = json.dumps(p).encode('utf-8')
    try:
        req =  request.Request("http://127.0.0.1:7860/prompt", data=data)
        request.urlopen(req)
        print("Prompt queued successfully")
    except Exception as e:
        print(f"Error queuing prompt: {e}")

class DwarfHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/dwarf':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                print("Received dwarf data")
                
                prompt_text = generate_prompt(data)
                print(f"Generated prompt: {prompt_text}")
                
                # Clone workflow
                current_workflow = copy.deepcopy(WORKFLOW)
                
                # Update prompt
                # Node 6 is CLIPTextEncode (Positive)
                if "6" in current_workflow and "inputs" in current_workflow["6"]:
                    current_workflow["6"]["inputs"]["text"] = prompt_text
                
                queue_prompt(current_workflow)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                try:
                    self.wfile.write(json.dumps({"status": "success", "prompt": prompt_text}).encode('utf-8'))
                except BrokenPipeError:
                    print("Client disconnected before response could be fully sent")
            except Exception as e:
                print(f"Error processing request: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=3000):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), DwarfHandler) as httpd:
        print(f"Serving at port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()