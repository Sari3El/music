# Prop packs given by the commissioner (second Dropbox folder): where they are, their real scale, how they are split into
# pieces and which texture files make their materials. Pure Python: read by prep_props.py (Blender) and kit_textures.py.
# Texture keys are regular expressions on the file names (the 32-hex prefix of the pack files is ignored).
# mode: whole = one piece; objects = one piece per object; clusters = loose parts joined when their boxes touch.
# Every piece is scaled to metres, turned z-up, its origin put at the centre of its footprint on the floor.

PACKS = {
    "Throne": dict(dir="ClockworkCreations/*Throne*", scale=100.0, mode="whole", folder="Props/Throne",
                   drop_objects=["Throne2"],                               # the stone base (socle) of the throne
                   drop_boxes=[[-0.70, -0.40, -0.66, -0.38, 0.0, 0.8]],    # candles on the floor, front-left
                   mats={"lambert8": "PR_Throne", "lambert7": "PR_ThroneDecor"}),
    "RugDark": dict(dir="ClockworkCreations/*Rugs*", scale=100.0, mode="objects", folder="Props/RugsDark", label=r"_Rug_Trimsheet1?_0$",
                    mats={"": "PR_RugDark"}),
    "RugLight": dict(dir="HawtorStudio/*Rug*", scale=100.0, mode="objects", folder="Props/RugsLight", label=r"^SM_|_Export.*$",
                     mats={"": "PR_RugLight"}),
    "Furniture": dict(dir="AntonChemezov/*Furniture*", scale=1000.0, mode="clusters", folder="Props/Furniture",
                      skip_objects=["Floor_Walls", "_Fire"],               # showcase room; flat flame cards (texture broken)
                      mats={"Bed_Cloth_Mat": "PR_FurnBedCloth", "Table_Cloth": "PR_FurnTableCloth", "Curtain_Mat": "PR_FurnCurtain",
                            "Bear_Skin": "PR_FurnBearSkin", "Backing_Box": "PR_FurnBox", "Barrel_Mat": "PR_FurnBarrel",
                            "Chest_Mat": "PR_FurnChest", "Tools_Mat": "PR_FurnTools", "Woods_Mat": "PR_FurnWoods",
                            "Lighter_Mat": "PR_FurnLighter", "Picture": "PR_FurnPictures",
                            "Furniture_Mat": "PR_Furniture"}),
    "Chandelier": dict(dir="KevinPopescu/*Chandelier*", scale=3.5, mode="whole", folder="Props/Chandelier", anchor="ceiling",
                       mats={"fire": "PR_ChandelierFire", "Chandelier": "PR_Chandelier"}),
    "Candelabra": dict(dir="NeverSleep/*Candelabra*", height=1.9, mode="whole", folder="Props/Candelabra",
                       mats={"": "PR_Candelabra"}),
    "Painting": dict(dir="yowi/*Paintings*", scale=100.0, mode="objects", folder="Props/Paintings", label=r"^cuadro_|_Cuadros_0$",
                     mats={"": "PR_Paintings"}),
    "Crucifixion": dict(dir="Privalov/*Crucifixion*", height=1.85, mode="whole", folder="Props/Crucifixion", stand_up=True,
                        mats={"": "PR_Bronze"}),
    "ChurchCross": dict(dir="nedo/*Cross*", height=3.2, mode="whole", folder="Props/ChurchCross",
                        mats={"": "PR_ChurchCross"}),
    "Coffin": dict(dir="BGavi/*Coffin*", scale=6.2, mode="whole", folder="Props/Coffin",
                   mats={"": "PR_Coffin"}),
    "Shack": dict(dir="ANRUVAL3DMODELS/*Shack*", scale=1.0, mode="whole", folder="Environment/Shack",
                  mats={"": "PR_WoodenShack"}),
}

# material: pack, D, N, R (None = no map), extras, fallback colour, physical surface, metallic, emissive, two-sided
# extras: dxn (DirectX normal), ao (multiplied into D), rough_from_spec (R = 1 - specular), alpha (D alpha / mask file),
# metal_map, emit (emissive map: the material glows where it is bright).
# Medieval Furniture Pack: thirteen of its texture files were delivered scrambled (8x8 blocks out of place: Floor_Bear, Barrel,
# Bed_Cloth, Table_Cloth, Curtain, Pictures, Picture_Desks, Lighter, Fire); their materials use a plain colour until clean
# files come (doc/props_et_textures.md).
MATS = {
    "PR_Throne": dict(pack="Throne", D=r"Base_color_1001", N=r"Normal_DirectX_1001", R=r"Roughness_1001", ao=r"Mixed_AO_1001",
                      dxn=True, col=(0.25, 0.24, 0.24), phys="Stone", metal=0.0),
    "PR_ThroneDecor": dict(pack="Throne", D=r"Base_color_1003", N=r"Normal_DirectX_1003", R=None, alpha=r"Opacity_1003",
                           emit=r"Emissive_1003", dxn=True, col=(0.6, 0.5, 0.4), phys="Wood", metal=0.0),
    "PR_RugDark": dict(pack="RugDark", D=r"Rug_Trimsheet_Base_color", N=r"Rug_Trimsheet_Normal_DirectX", R=r"Rug_Trimsheet_Roughness",
                       dxn=True, col=(0.35, 0.15, 0.12), phys="Wood", two=True),
    "PR_RugLight": dict(pack="RugLight", D=r"T_Rug_Pack_Color", N=r"T_Rug_Pack_Normal", R=r"M_Rug_Pack_Roughness",
                        col=(0.6, 0.52, 0.38), phys="Wood", two=True),
    "PR_Furniture": dict(pack="Furniture", D=r"RGB_Furniture_Diffuse", N=r"N_Furniture_Normal", R=None, ao=r"R_Furniture_AO", col=(0.35, 0.25, 0.16), phys="Wood"),
    "PR_FurnWoods": dict(pack="Furniture", D=r"RGB_Woods_Diffuse", N=r"N_Woods_Normal", R=None, ao=r"R_Woods_AO", col=(0.35, 0.25, 0.16), phys="Wood"),
    "PR_FurnBox": dict(pack="Furniture", D=r"RGB_Backing_Box_Diffuse", N=r"RGB_Backing_Box_Normals", R=None, ao=r"RGB_Backing_Box_AO", col=(0.35, 0.25, 0.16), phys="Wood"),
    "PR_FurnBearSkin": dict(pack="Furniture", D=None, N=None, R=None, col=(0.1, 0.07, 0.05), phys="Wood", two=True),
    "PR_FurnChest": dict(pack="Furniture", D=r"RGB_Chest_Diffuse", N=r"N_Chest_Normals", R=None, ao=r"R_Chest_AO", col=(0.35, 0.25, 0.16), phys="Wood"),
    "PR_FurnTools": dict(pack="Furniture", D=r"RGB_Tools", N=r"N_Tools_Normal", R=None, col=(0.3, 0.27, 0.24), phys="Metal", metal=0.4),
    "PR_FurnBarrel": dict(pack="Furniture", D=None, N=None, R=None, col=(0.3, 0.22, 0.14), phys="Wood"),
    "PR_FurnCurtain": dict(pack="Furniture", D=None, N=r"R_Cloth_Normal", R=None, col=(0.4, 0.1, 0.08), phys="Wood", two=True),
    "PR_FurnBedCloth": dict(pack="Furniture", D=None, N=r"R_Cloth_Normal", R=None, col=(0.4, 0.1, 0.07), phys="Wood", two=True),
    "PR_FurnTableCloth": dict(pack="Furniture", D=None, N=r"R_Cloth_Normal", R=None, col=(0.45, 0.12, 0.08), phys="Wood", two=True),
    "PR_FurnPictures": dict(pack="Furniture", D=None, N=None, R=None, col=(0.4, 0.3, 0.2), phys="Wood"),
    "PR_FurnLighter": dict(pack="Furniture", D=None, N=None, R=None, col=(0.16, 0.12, 0.09), phys="Wood"),
    "PR_Chandelier": dict(pack="Chandelier", D=r"Chandelier_SHD_albedo", N=r"Chandelier_SHD_normal", R=r"Chandelier_SHD_roughness",
                          ao=r"Chandelier_SHD_AO", metal_map=r"Chandelier_SHD_metallic", col=(0.2, 0.18, 0.16), phys="Metal", metal=0.6),
    "PR_ChandelierFire": dict(pack="Chandelier", D=r"RGB_albedo", N=None, R=None, alpha=r"R_alpha", emit="D", col=(1.0, 0.6, 0.25), phys="Wood", two=True),
    "PR_Candelabra": dict(pack="Candelabra", D=r"lambert4_albedo", N=r"lambert4_normal", R=r"lambert4_roughness", ao=r"lambert4_AO",
                          metal_map=r"lambert4_metallic", col=(0.15, 0.13, 0.12), phys="Metal", metal=0.6),
    "PR_Paintings": dict(pack="Painting", D=r"RGB_cuadros", N=None, R=None, col=(0.4, 0.32, 0.22), phys="Wood"),
    "PR_Bronze": dict(pack="Crucifixion", D=None, N=None, R=None, col=(0.55, 0.33, 0.2), phys="Metal", metal=1.0, rough=0.35),
    "PR_ChurchCross": dict(pack="ChurchCross", D=r"RGB_sketchfabTemp", N=None, R=None, col=(0.3, 0.35, 0.3), phys="Metal", metal=0.5),
    "PR_Coffin": dict(pack="Coffin", D=r"Coffin_2_Color_Map", N=r"Coffin_2_Normal_Map2", R=r"Coffin_2_Specular_Map", rough_from_spec=True,
                      col=(0.35, 0.37, 0.38), phys="Stone"),
    "PR_WoodenShack": dict(pack="Shack", D=r"Wooden_Shack_AlbedoTransparency", N=r"Wooden_Shack_Normal", R=None, alpha="D",
                           col=(0.35, 0.27, 0.2), phys="Wood", two=True),
}

# pieces of the furniture showcase (clusters): box corner `lo` in the showcase (metres, Blender axes, as found by
# props_split_probe), name, turn (degrees, so that the front of the piece faces +X), skip = left out
FURN = [
    dict(lo=[5.395, 2.036, -0.001], name="Oven", yaw=180),                    # stone bread oven with its woodpile
    dict(lo=[3.708, -2.0, -0.007], name="Bed"),
    dict(lo=[2.019, -1.949, 0.006], name="Settle"),                           # bench with a back
    dict(lo=[1.971, -4.668, -0.001], name="Cupboard"),
    dict(lo=[1.917, 3.703, 0.013], name="LowShelfA"),
    dict(lo=[3.926, -4.121, 0.011], name="Chest"),
    dict(lo=[1.947, 2.64, 0.006], name="LowShelfB"),
    dict(lo=[1.941, 1.836, 0.009], name="LowShelfC"),
    dict(lo=[5.718, -0.648, 0.038], name="ClothTable"),
    dict(lo=[5.824, -4.107, 0.106], name="Bench"),
    dict(lo=[6.038, 1.27, 0.559], name="WallShelf", yaw=180, anchor="floor0"),  # hung at 0.56 m
    dict(lo=[1.954, 0.37, -0.002], name="CrateLamp"),
    dict(lo=[5.914, 0.641, 0.013], name="Chair", yaw=-90),
    dict(lo=[5.838, -1.884, 0.053], name="Table"),
    dict(lo=[4.32, 4.213, 0.0], name="Mallet", yaw=-90),
    dict(lo=[3.702, 0.682, 0.019], name="Trapdoor"),
    dict(lo=[3.324, 4.212, 0.013], name="Churn", yaw=-90),
    dict(lo=[5.097, 4.099, 0.007], name="Hoe", yaw=-90),
    dict(lo=[2.016, -2.646, 0.014], name="TorchStand"),
    dict(lo=[4.755, 4.221, -0.005], name="Shovel", yaw=-90),
    dict(lo=[3.878, 4.263, -0.001], name="Axe", yaw=-90),
    dict(lo=[5.91, 1.407, 0.01], name="Stool"),
    dict(lo=[3.143, -5.041, 1.146], name="CornerShelfHigh", anchor="floor0"),
    dict(lo=[1.748, 1.723, 0.818], name="CornerShelfLow", anchor="floor0"),
    dict(lo=[3.503, -5.155, 0.437], name="TowelRack", skip=True),           # its cloth texture is broken
    dict(lo=[2.743, 4.167, 0.007], name="Tub"),
    dict(lo=[2.652, 0.459, 1.308], name="PlateRack", anchor="floor0"),
    dict(lo=[3.112, -5.044, 0.337], name="LongShelf", yaw=90, anchor="floor0"),
    dict(lo=[1.682, -1.117, 1.121], name="WallLamp", anchor="floor0"),
    dict(lo=[2.803, 1.914, 0.016], name="BearSkin"),
    dict(lo=[6.362, -3.852, 0.822], name="PictureSmall", skip=True),         # picture textures broken
    dict(lo=[6.322, -3.071, 0.783], name="PictureMiddle", skip=True),
]
