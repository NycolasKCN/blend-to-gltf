"""
export_animations.py
-----------------------
Exporta a Armature com seu animation clip atual para .glb.

USO:
  blender --background --python export_animations.py -- input.blend -o saida.glb

OPÇÕES:
  --output, -o        Caminho do arquivo .glb de saída (padrão: animations.glb)
  --armature-name     Nome da armature no arquivo .blend (padrão: "Armature.001")
  --verbose           Imprime detalhes da action encontrada
"""

import bpy
import sys
import os
import argparse


def parse_args():
    argv = sys.argv
    if "--" not in argv:
        print("ERRO: Passe os argumentos após '--'")
        sys.exit(1)

    script_args = argv[argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("blend_file", metavar="BLEND")
    parser.add_argument("--output", "-o", default="animations.glb")
    parser.add_argument("--armature-name", default="Armature.001")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(script_args)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_armature(filepath: str, armature_name: str, verbose: bool):
    filepath = os.path.abspath(filepath)

    with bpy.data.libraries.load(filepath, link=False) as (src, dst):
        if verbose:
            print(f"  Objetos disponíveis: {list(src.objects)}")
        dst.objects = list(src.objects)
        dst.actions = list(src.actions)

    scene = bpy.context.scene
    arm_obj = None

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and (armature_name == "" or obj.name == armature_name):
            if obj.name not in [o.name for o in scene.collection.objects]:
                scene.collection.objects.link(obj)
            arm_obj = obj
            break

    if arm_obj is None:
        print(f"  [ERRO] Armature '{armature_name}' não encontrada.")
        return None

    # Remove tudo que não é a armature alvo
    for obj in list(bpy.data.objects):
        if obj != arm_obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    print(f"  Armature: '{arm_obj.name}' ({len(arm_obj.data.bones)} bones)")

    # Reporta a action já atribuída (se houver)
    if arm_obj.animation_data and arm_obj.animation_data.action:
        action = arm_obj.animation_data.action
        print(f"  Action ativa: '{action.name}' "
              f"({int(action.frame_range[0])}–{int(action.frame_range[1])} frames)")
    else:
        print("  [AVISO] Nenhuma action diretamente atribuída à armature.")

    return arm_obj


def export_glb(output_path: str):
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        export_animations=True,
        export_nla_strips=False,
        export_def_bones=False,
        export_apply=False,
        export_cameras=False,
        export_lights=False,
        export_materials='NONE',
        export_morph=False,
        use_selection=False,
    )
    print(f"GLB exportado: {output_path}")


def main():
    args = parse_args()

    print("\n" + "=" * 50)
    print("  Export Armature + Animation → GLB")
    print("=" * 50)
    print(f"  Blender   : {bpy.app.version_string}")
    print(f"  Armature  : '{args.armature_name}'")
    print(f"  Entrada   : {args.blend_file}")
    print(f"  Saída     : {args.output}")
    print("=" * 50)

    reset_scene()

    print(f"\n→ Importando: {os.path.basename(args.blend_file)}")
    arm_obj = import_armature(args.blend_file, args.armature_name, args.verbose)

    if arm_obj is None:
        print("\nERRO: Armature não encontrada. Use --armature-name para especificar o nome.")
        sys.exit(1)

    print("\n→ Exportando GLB...")
    export_glb(args.output)
    print("\n✓ Concluído!\n")


if __name__ == "__main__":
    main()
