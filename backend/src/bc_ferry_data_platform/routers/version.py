from importlib.metadata import version

from fastapi import APIRouter

router = APIRouter(prefix="/version")

'''
Get the current backend version, maintained by release-please using conventional commits
'''
@router.get("/")
def get_version() -> dict[str, str]:
    return {"version": version("bc-ferry-data-platform")}