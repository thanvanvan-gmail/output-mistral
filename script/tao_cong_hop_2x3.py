import ifcopenshell
import time
import uuid

OUT = "/workspace/github__thanvanvan-gmail__output-mistral/ifc/cong_hop_2x3x10_IFC4.ifc"

# Thong so cong hop: khau do thong 2.0m (X) x 3.0m (Y), dai 10m (Z), thanh day 0.3m
DAI = 10.0
RONG_TRONG = 2.0
CAO_TRONG = 3.0
DAY = 0.3
KLR_BETONG = 2400.0  # kg/m3

f = ifcopenshell.file(schema="IFC4")

def gid(seed):
    return ifcopenshell.guid.compress(str(uuid.uuid5(uuid.NAMESPACE_DNS, seed)))

# ---------- Header ----------
now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
f.header.file_name.name = "cong_hop_2x3x10_IFC4.ifc"
f.header.file_name.time_stamp = now
f.header.file_name.author = ("Nguyen Van A",)
f.header.file_name.organization = ("Cong ty Tu van BIM",)
f.header.file_name.preprocessor_version = "ifcopenshell 0.9.0"
f.header.file_name.originating_system = "tao_cong_hop_2x3.py"
f.header.file_name.authorization = "Nguyen Van A"
f.header.file_description.description = ("IFC4 - Cong hop BTCT khau do 2m x 3m, dai 10m",)
f.header.file_description.implementation_level = "2;1"
f.header.file_schema.schema_identifiers = ("IFC4",)

# ---------- Owner history ----------
person = f.create_entity("IfcPerson", FamilyName="Nguyen", GivenName="Van A")
org = f.create_entity("IfcOrganization", Name="Cong ty Tu van BIM")
pao = f.create_entity("IfcPersonAndOrganization", ThePerson=person, TheOrganization=org)
app = f.create_entity("IfcApplication", ApplicationDeveloper=org, Version="1.0",
                      ApplicationFullName="tao_cong_hop_2x3.py", ApplicationIdentifier="CONGHOP")
oh = f.create_entity("IfcOwnerHistory", OwningUser=pao, OwningApplication=app,
                     State="READWRITE", ChangeAction="ADDED", CreationDate=int(time.time()))

# ---------- Units ----------
ua = f.create_entity("IfcUnitAssignment", Units=[
    f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    f.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE"),
    f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE"),
    f.create_entity("IfcSIUnit", UnitType="PLANEANGLEUNIT", Name="RADIAN"),
])

# ---------- Context ----------
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextIdentifier=None, ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))),
                      TrueNorth=f.create_entity("IfcDirection", DirectionRatios=(0.0, 1.0)))
sub = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body", ContextType="Model",
                      ParentContext=ctx, TargetScale=1.0, TargetView="MODEL_VIEW")

# ---------- Spatial structure ----------
project = f.create_entity("IfcProject", GlobalId=gid("project-conghop"), OwnerHistory=oh,
                          Name="Cong hop 2m x 3m dai 10m", Description="BTCT Mac 300",
                          UnitsInContext=ua, RepresentationContexts=[ctx])

def axis3(loc):
    return f.create_entity("IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=loc),
        Axis=f.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
        RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0)))

site_pl = f.create_entity("IfcLocalPlacement", PlacementRelTo=None, RelativePlacement=axis3((0.0, 0.0, 0.0)))
site = f.create_entity("IfcSite", GlobalId=gid("site"), OwnerHistory=oh, Name="Cong hop",
                       ObjectPlacement=site_pl)
bld_pl = f.create_entity("IfcLocalPlacement", PlacementRelTo=site_pl, RelativePlacement=axis3((0.0, 0.0, 0.0)))
bld = f.create_entity("IfcBuilding", GlobalId=gid("building"), OwnerHistory=oh, Name="Than cong",
                      ObjectPlacement=bld_pl)
st_pl = f.create_entity("IfcLocalPlacement", PlacementRelTo=bld_pl, RelativePlacement=axis3((0.0, 0.0, 0.0)))
storey = f.create_entity("IfcBuildingStorey", GlobalId=gid("storey"), OwnerHistory=oh,
                         Name="Cao do tuyet doi", Elevation=0.0, ObjectPlacement=st_pl)
f.create_entity("IfcRelAggregates", GlobalId=gid("rel-p-s"), OwnerHistory=oh,
                RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=gid("rel-s-b"), OwnerHistory=oh,
                RelatingObject=site, RelatedObjects=[bld])
f.create_entity("IfcRelAggregates", GlobalId=gid("rel-b-st"), OwnerHistory=oh,
                RelatingObject=bld, RelatedObjects=[storey])

# ---------- Material ----------
mat = f.create_entity("IfcMaterial", Name="BTCT Mac 300")

# ---------- Group ----------
group = f.create_entity("IfcGroup", GlobalId=gid("group-conghop"), OwnerHistory=oh,
                        Name="Cong hop 2x3x10 - BTCT M300")

# ---------- Helper ----------
def make_box(name, ifc_class, mark, xdim, ydim, loc, predefined):
    prof = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA",
        Position=f.create_entity("IfcAxis2Placement2D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0))),
        XDim=xdim, YDim=ydim)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=prof,
        Position=f.create_entity("IfcAxis2Placement3D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))),
        ExtrudedDirection=f.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
        Depth=DAI)
    style = f.create_entity("IfcPresentationStyleAssignment", Styles=[
        f.create_entity("IfcSurfaceStyle", Name="BTCT M300", Side="BOTH", Styles=[
            f.create_entity("IfcSurfaceStyleRendering",
                SurfaceColour=f.create_entity("IfcColourRgb", Red=0.75, Green=0.75, Blue=0.75),
                Transparency=0.0, ReflectanceMethod="NOTDEFINED")])])
    styled = f.create_entity("IfcStyledItem", Item=solid, Styles=[style])
    rep = f.create_entity("IfcShapeRepresentation", ContextOfItems=sub, RepresentationIdentifier="Body",
                          RepresentationType="SweptSolid", Items=[solid])
    shape = f.create_entity("IfcProductDefinitionShape", Representations=[rep])
    pl = f.create_entity("IfcLocalPlacement", PlacementRelTo=st_pl, RelativePlacement=axis3(loc))
    el = f.create_entity(ifc_class, GlobalId=gid("el-" + mark), OwnerHistory=oh, Name=name,
                         Description=mark, ObjectPlacement=pl, Representation=shape,
                         PredefinedType=predefined)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=gid("mat-" + mark), OwnerHistory=oh,
                    RelatedObjects=[el], RelatingMaterial=mat)
    vol = xdim * ydim * DAI
    mass = vol * KLR_BETONG
    props = [
        f.create_entity("IfcPropertySingleValue", Name="Mark", NominalValue=f.create_entity("IfcLabel", mark)),
        f.create_entity("IfcPropertySingleValue", Name="VatLieu", NominalValue=f.create_entity("IfcLabel", "BTCT Mac 300")),
        f.create_entity("IfcPropertySingleValue", Name="MacBeTong", NominalValue=f.create_entity("IfcLabel", "300")),
        f.create_entity("IfcPropertySingleValue", Name="TheTich_m3", NominalValue=f.create_entity("IfcVolumeMeasure", round(vol, 4))),
        f.create_entity("IfcPropertySingleValue", Name="KhoiLuong_kg", NominalValue=f.create_entity("IfcMassMeasure", round(mass, 1))),
        f.create_entity("IfcPropertySingleValue", Name="ChieuDai_m", NominalValue=f.create_entity("IfcLengthMeasure", DAI)),
    ]
    pset = f.create_entity("IfcPropertySet", GlobalId=gid("pset-" + mark), OwnerHistory=oh,
                           Name="Pset_CongHop", HasProperties=props)
    f.create_entity("IfcRelDefinesByProperties", GlobalId=gid("rel-" + mark), OwnerHistory=oh,
                    RelatedObjects=[el], RelatingPropertyDefinition=pset)
    qprops = [
        f.create_entity("IfcQuantityVolume", Name="NetVolume", VolumeValue=round(vol, 4)),
        f.create_entity("IfcQuantityWeight", Name="NetWeight", WeightValue=round(mass, 1)),
        f.create_entity("IfcQuantityLength", Name="Length", LengthValue=DAI),
    ]
    qset = f.create_entity("IfcElementQuantity", GlobalId=gid("qset-" + mark), OwnerHistory=oh,
                           Name="Qto_CongHop", Quantities=qprops)
    f.create_entity("IfcRelDefinesByProperties", GlobalId=gid("qrel-" + mark), OwnerHistory=oh,
                    RelatedObjects=[el], RelatingPropertyDefinition=qset)
    return el, vol, mass

rong_ngoai = RONG_TRONG + 2 * DAY
# mat cat ngang: X = rong, Y = cao; extrude theo Z (dai cong)
elems = []
e, v, m = make_box("Ban day", "IfcSlab", "CONG-DAY", rong_ngoai, DAY, (0.0, DAY / 2, 0.0), "FLOOR")
elems.append((e, v, m))
e, v, m = make_box("Nap cong", "IfcSlab", "CONG-NAP", rong_ngoai, DAY, (0.0, DAY + CAO_TRONG + DAY / 2, 0.0), "ROOF")
elems.append((e, v, m))
e, v, m = make_box("Tuong trai", "IfcWall", "CONG-TUONG-TRAI", DAY, CAO_TRONG,
                   (-(RONG_TRONG / 2 + DAY / 2), DAY + CAO_TRONG / 2, 0.0), "STANDARD")
elems.append((e, v, m))
e, v, m = make_box("Tuong phai", "IfcWall", "CONG-TUONG-PHAI", DAY, CAO_TRONG,
                   ((RONG_TRONG / 2 + DAY / 2), DAY + CAO_TRONG / 2, 0.0), "STANDARD")
elems.append((e, v, m))

f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=gid("rel-contain"), OwnerHistory=oh,
                RelatingStructure=storey, RelatedElements=[e for e, _, _ in elems])
f.create_entity("IfcRelAssignsToGroup", GlobalId=gid("rel-group"), OwnerHistory=oh,
                RelatingGroup=group, RelatedObjects=[e for e, _, _ in elems])

f.write(OUT)

# ---------- Tu kiem ----------
tv = sum(v for _, v, _ in elems)
tm = sum(m for _, _, m in elems)
print(f"Da ghi: {OUT}")
print(f"So cau kien: {len(elems)} | Tong the tich: {tv:.3f} m3 | Tong khoi luong: {tm:,.0f} kg ({tm/1000:.2f} tan)")

chk = ifcopenshell.open(OUT)
els = chk.by_type("IfcElement")
print(f"Kiem lai: {len(els)} IfcElement trong file")
import ifcopenshell.geom
n_ok = 0
for el in els:
    s = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), el)
    n_ok += 1
print(f"Hinh hoc tao duoc: {n_ok}/{len(els)}")
