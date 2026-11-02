import re, base64, gzip, json, struct, math, uuid
import numpy as np
import ifcopenshell
from ifcopenshell.util.element import get_psets

HTML = "CBN_mo_hinh.html"  # duong dan toi file HTML nguon
OUT = "CBN_mo_hinh.ifc"

html = open(HTML, encoding="utf-8").read()
m = re.search(r'<script id="du_lieu" type="application/octet-stream">(.*?)</script>', html, re.S)
raw = gzip.decompress(base64.b64decode(m.group(1).strip()))
assert raw[:4] == b"CBN1"
n = struct.unpack_from("<I", raw, 4)[0]
hdr = json.loads(raw[8:8+n].decode("utf-8"))
meta, elems, meshes = hdr["meta"], hdr["elems"], hdr["meshes"]

off = 8 + n
off += (-off) % 4
tot_nv = sum(mm[1] for mm in meshes)
tot_ni = sum(mm[2] for mm in meshes)
verts = np.frombuffer(raw, dtype="<i4", count=tot_nv*3, offset=off).reshape(tot_nv, 3).astype(np.float64)
off += tot_nv*3*4
idx = np.frombuffer(raw, dtype="<i4", count=tot_ni, offset=off).copy()

verts = verts.reshape(-1)
for j in range(3, verts.size):
    verts[j] += verts[j-3]
verts = verts.reshape(tot_nv, 3) * 0.001

mesh_verts, mesh_idx = {}, {}
vi, ii = 0, 0
for key, nv, ni in meshes:
    mesh_verts[key] = verts[vi:vi+nv]
    a = idx[ii:ii+ni]
    for j in range(1, ni):
        a[j] += a[j-1]
    mesh_idx[key] = a.reshape(-1, 3)
    vi += nv; ii += ni

REVIT_ANG = math.radians(float(meta["goc_revit_X"]))
Rz = np.array([[math.cos(-REVIT_ANG), -math.sin(-REVIT_ANG), 0.0],
               [math.sin(-REVIT_ANG),  math.cos(-REVIT_ANG), 0.0],
               [0.0, 0.0, 1.0]])

def ifc_guid(revit_id):
    u = uuid.uuid5(uuid.NAMESPACE_URL, "CBN-%d" % revit_id)
    return base64.b64encode(u.bytes).decode("ascii").replace("=", "")

def elem_transform(e):
    if "o" not in e and "t" not in e:
        return np.eye(3), np.zeros(3)
    if "o" in e:
        R = np.eye(3)
        t = np.array(e["o"], dtype=float) * 0.001
    else:
        t12 = e["t"]
        R = np.array([[t12[0], t12[3], t12[6]],
                      [t12[1], t12[4], t12[7]],
                      [t12[2], t12[5], t12[8]]])
        t = np.array(t12[9:12], dtype=float)
    return Rz @ R, Rz @ t

def map_element(e):
    fam, cat, mark = e["fam"], e["cat"], e["mark"]
    if "Pile" in fam:
        return "IfcPile", ("DRIVEN", "PRECAST_CONCRETE")
    if "Girder_InvertedT" in fam:
        return "IfcBeam", "T_BEAM"
    if "CapBeam" in fam or "PierCap" in fam:
        return "IfcBeam", "NOTDEFINED"
    if "FenderCap" in fam or "AbutmentFooting" in fam:
        return "IfcFooting", "PILE_CAP"
    if cat == "Walls" or "Wall" in fam:
        return "IfcWall", "NOTDEFINED"
    if "BaseSlab" in fam or "SealingConcrete" in fam:
        return "IfcSlab", "BASESLAB"
    if cat == "Floors" or "Slab" in fam:
        return "IfcSlab", "FLOOR"
    if cat == "Railings":
        return "IfcRailing", "GUARDRAIL"
    if cat == "Top Rails" or mark.endswith("/TR"):
        return "IfcRailing", "HANDRAIL"
    if cat == "Lighting Fixtures":
        return "IfcLightFixture", "NOTDEFINED"
    if "Cylinder" in fam:
        return "IfcActuator", "HYDRAULICACTUATOR"
    return "IfcBuildingElementProxy", "NOTDEFINED"

MAT_COLORS = {
    "PCC_Concrete_M30": (0.62, 0.62, 0.62),
    "PCC_Concrete_M300": (0.78, 0.77, 0.74),
    "PCC_Concrete_M200": (0.68, 0.65, 0.62),
    "PCC_Asphalt": (0.16, 0.16, 0.17),
    "PCC_Steel": (0.45, 0.47, 0.52),
    "PCC_Steel_Galvanized": (0.72, 0.73, 0.75),
    "PCC_Steel_SheetPile": (0.42, 0.36, 0.30),
    "PCC_Steel_Stainless": (0.86, 0.86, 0.89),
    "PCC_Stone_Gabion": (0.55, 0.51, 0.42),
}

f = ifcopenshell.file(schema="IFC4")
now = int(__import__("time").time())

person = f.create_entity("IfcPerson", FamilyName="PORTCOAST", GivenName="BIM Team")
org = f.create_entity("IfcOrganization", Name="PORTCOAST CONSULTANT CORPORATION")
po = f.create_entity("IfcPersonAndOrganization", ThePerson=person, TheOrganization=org)
app = f.create_entity("IfcApplication", ApplicationDeveloper=org, Version="1.0",
                      ApplicationFullName="CBN HTML to IFC converter", ApplicationIdentifier="CBN2IFC")
owner = f.create_entity("IfcOwnerHistory", OwningUser=po, OwningApplication=app,
                        State="READWRITE", ChangeAction="ADDED", CreationDate=now)

f.header.file_description.description = ("ViewDefinition [CoordinationView_V2.0]; mo hinh cong kiem soat trieu rach Binh Nham",
                                        "Chuyen tu mo hinh nhung trong HTML")
f.header.file_name.name = "CBN_mo_hinh.ifc"
f.header.file_name.time_stamp = meta.get("ngay", "2026-10-31T00:00:00")
f.header.file_name.author = "PORTCOAST BIM Team"
f.header.file_name.organization = "PORTCOAST CONSULTANT CORPORATION"
f.header.file_name.preprocessor_version = "CBN2IFC 1.0 (IfcOpenShell %s)" % ifcopenshell.version
f.header.file_name.originating_system = "Revit -> HTML embed -> IFC4"
f.header.file_name.authorization = "PORTCOAST"
f.header.file_schema.schema_identifiers = ("IFC4",)

si = lambda u: f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Prefix=None, Name=u) if u != "METRE" else \
    f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
units = f.create_entity("IfcUnitAssignment", Units=[
    f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    f.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE"),
    f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE"),
    f.create_entity("IfcSIUnit", UnitType="PLANEANGLEUNIT", Name="RADIAN"),
])

ctx = f.create_entity("IfcGeometricRepresentationContext", ContextIdentifier=None,
                      ContextType="Model", CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))),
                      TrueNorth=f.create_entity("IfcDirection", DirectionRatios=(0.0, 1.0)))
sub = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                      ContextType="Model", ParentContext=ctx,
                      TargetScale=1.0, TargetView="MODEL_VIEW",
                      UserDefinedTargetView="MODEL_VIEW")

vn = meta["vn2000"]
alpha = math.radians(float(vn["goc_deg"]))
crs = f.create_entity("IfcProjectedCRS", Name="VN2000", Description="VN2000 / UTM zone 48N",
                      GeodeticDatum="VN2000",
                      MapUnit=f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"))
mapconv = f.create_entity("IfcMapConversion", SourceCRS=None, TargetCRS=crs,
                          Eastings=float(vn["E"]), Northings=float(vn["N"]),
                          OrthogonalHeight=0.0, XAxisAbscissa=math.cos(alpha), XAxisOrdinate=math.sin(alpha),
                          Scale=1.0)


project = f.create_entity("IfcProject", GlobalId=ifc_guid(1), OwnerHistory=owner, Name=meta["ten"],
                          Description="Cong kiem sousat trieu rach Binh Nham", ObjectType=None,
                          LongName=None, Phase=None, RepresentationContexts=[ctx], UnitsInContext=units)
site = f.create_entity("IfcSite", GlobalId=ifc_guid(2), OwnerHistory=owner, Name="Hien truong",
                       ObjectType=None, ObjectPlacement=f.create_entity("IfcLocalPlacement"),
                       Representation=None, LongName=None, CompositionType="ELEMENT",
                       RefLatitude=None, RefLongitude=None, RefElevation=None, LandTitleNumber=None,
                       SiteAddress=None)
bldg = f.create_entity("IfcBuilding", GlobalId=ifc_guid(3), OwnerHistory=owner, Name="Cong Binh Nham",
                       ObjectType=None, ObjectPlacement=f.create_entity("IfcLocalPlacement"),
                       Representation=None, LongName=None, CompositionType="ELEMENT",
                       ElevationOfRefHeight=None, ElevationOfTerrain=None, BuildingAddress=None)
storey = f.create_entity("IfcBuildingStorey", GlobalId=ifc_guid(4), OwnerHistory=owner,
                         Name="Cao do tuyet doi", ObjectType=None,
                         ObjectPlacement=f.create_entity("IfcLocalPlacement"),
                         Representation=None, LongName=None, CompositionType="ELEMENT", Elevation=0.0)
f.create_entity("IfcRelAggregates", GlobalId=ifc_guid(5), OwnerHistory=owner, RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=ifc_guid(6), OwnerHistory=owner, RelatingObject=site, RelatedObjects=[bldg])
f.create_entity("IfcRelAggregates", GlobalId=ifc_guid(7), OwnerHistory=owner, RelatingObject=bldg, RelatedObjects=[storey])

mat_cache, style_cache, rep_cache = {}, {}, {}
def get_material(mat):
    if mat not in mat_cache:
        mat_cache[mat] = f.create_entity("IfcMaterial", Name=mat, Category="PCC")
    return mat_cache[mat]

def get_rep(mesh_key, mat):
    ck = (mesh_key, mat)
    if ck in rep_cache:
        return rep_cache[ck]
    v = mesh_verts[mesh_key]
    tri = mesh_idx[mesh_key]
    pts = f.create_entity("IfcCartesianPointList3D", CoordList=[[float(x), float(y), float(z)] for x, y, z in v])
    tfs = f.create_entity("IfcTriangulatedFaceSet", CoordIndex=[[int(a)+1, int(b)+1, int(c)+1] for a, b, c in tri],
                          Coordinates=pts, Closed=False)
    col = MAT_COLORS.get(mat, (0.7, 0.7, 0.7))
    style = f.create_entity("IfcSurfaceStyle", Side="POSITIVE", Styles=[
        f.create_entity("IfcSurfaceStyleShading", SurfaceColour=f.create_entity(
            "IfcColourRgb", Red=col[0], Green=col[1], Blue=col[2]), Transparency=0.0)])
    styled = f.create_entity("IfcStyledItem", Item=tfs, Styles=[f.create_entity("IfcPresentationStyleAssignment", Styles=[style])])
    rm = f.create_entity("IfcRepresentationMap", MappingOrigin=f.create_entity(
        "IfcAxis2Placement3D", Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))),
        MappedRepresentation=f.create_entity("IfcShapeRepresentation", ContextOfItems=sub,
            RepresentationIdentifier="Body", RepresentationType="Tessellation", Items=[tfs]))
    mapped = f.create_entity("IfcMappedItem", MappingSource=rm,
        MappingTarget=f.create_entity("IfcCartesianTransformationOperator3D",
            Axis1=f.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0)),
            Axis2=f.create_entity("IfcDirection", DirectionRatios=(0.0, 1.0, 0.0)),
            LocalOrigin=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
            Scale=1.0, Axis3=f.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))))
    f.create_entity("IfcStyledItem", Item=mapped, Styles=[f.create_entity("IfcPresentationStyleAssignment", Styles=[style])])
    rep = f.create_entity("IfcShapeRepresentation", ContextOfItems=sub, RepresentationIdentifier="Body",
                          RepresentationType="MappedGeometry", Items=[mapped])
    rep_cache[ck] = rep
    return rep

groups = {}
group_ids = {}
for e in elems:
    eid = e["id"]
    cls, ptype = map_element(e)
    extra_attr = None
    if isinstance(ptype, tuple):
        ptype, extra_attr = ptype
    R, t = elem_transform(e)
    ax = f.create_entity("IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=(float(t[0]), float(t[1]), float(t[2]))),
        Axis=f.create_entity("IfcDirection", DirectionRatios=(float(R[2,0]), float(R[2,1]), float(R[2,2]))),
        RefDirection=f.create_entity("IfcDirection", DirectionRatios=(float(R[0,0]), float(R[0,1]), float(R[0,2]))))
    lp = f.create_entity("IfcLocalPlacement", PlacementRelTo=None, RelativePlacement=ax)
    rep = get_rep(e["mesh"], e["mat"])
    shape = f.create_entity("IfcProductDefinitionShape", Representations=[rep])
    kwargs = dict(GlobalId=ifc_guid(eid), OwnerHistory=owner, Name=e["mark"],
                  Description=e.get("com") or None, ObjectType=e["type"],
                  ObjectPlacement=lp, Representation=shape, Tag=None, PredefinedType=ptype)
    if extra_attr == "PRECAST_CONCRETE":
        kwargs["ConstructionType"] = "PRECAST_CONCRETE"
    el = f.create_entity(cls, **kwargs)
    pset = f.create_entity("IfcPropertySet", GlobalId=ifc_guid(eid + 10**9), OwnerHistory=owner, Name="CBN_ThongTin", HasProperties=[
        f.create_entity("IfcPropertySingleValue", Name="Mark", NominalValue=f.create_entity("IfcLabel", str(e["mark"]))),
        f.create_entity("IfcPropertySingleValue", Name="IdRevit", NominalValue=f.create_entity("IfcInteger", int(eid))),
        f.create_entity("IfcPropertySingleValue", Name="Category", NominalValue=f.create_entity("IfcLabel", e["cat"])),
        f.create_entity("IfcPropertySingleValue", Name="Family", NominalValue=f.create_entity("IfcLabel", e["fam"])),
        f.create_entity("IfcPropertySingleValue", Name="Type", NominalValue=f.create_entity("IfcLabel", e["type"])),
        f.create_entity("IfcPropertySingleValue", Name="VatLieu", NominalValue=f.create_entity("IfcLabel", e["mat"])),
        f.create_entity("IfcPropertySingleValue", Name="GhiChu", NominalValue=f.create_entity("IfcLabel", e.get("com") or "")),
    ])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=ifc_guid(eid + 2*10**9), OwnerHistory=owner,
                    RelatedObjects=[el], RelatingPropertyDefinition=pset)
    qprops = [f.create_entity("IfcQuantityVolume", Name="NetVolume", VolumeValue=float(e["vol"]), Unit=None)]
    if e.get("len"):
        qprops.append(f.create_entity("IfcQuantityLength", Name="Length", LengthValue=float(e["len"]), Unit=None))
    qto = f.create_entity("IfcElementQuantity", GlobalId=ifc_guid(eid + 3*10**9), OwnerHistory=owner, Name="Qto_CBN", Quantities=qprops)
    f.create_entity("IfcRelDefinesByProperties", GlobalId=ifc_guid(eid + 4*10**9), OwnerHistory=owner,
                    RelatedObjects=[el], RelatingPropertyDefinition=qto)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=ifc_guid(eid + 5*10**9), OwnerHistory=owner,
                    RelatedObjects=[el], RelatingMaterial=get_material(e["mat"]))
    if e["cat"] not in groups:
        groups[e["cat"]] = []
        group_ids[e["cat"]] = (hash(e["cat"]) % 10**9 + 10**10)
    groups[e["cat"]].append(el)

rel_elems = []
for cat, els in groups.items():
    g = f.create_entity("IfcGroup", GlobalId=ifc_guid(group_ids[cat]), OwnerHistory=owner, Name=cat,
                        Description="Hang muc: " + cat, ObjectType=None)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=ifc_guid(group_ids[cat] + 1), OwnerHistory=owner,
                    RelatingGroup=g, RelatedObjects=els)
    rel_elems.extend(els)
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=ifc_guid(999999999), OwnerHistory=owner,
                RelatingStructure=storey, RelatedElements=rel_elems)

f.write(OUT)
print("written", OUT)
