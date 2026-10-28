const zh = {
  title: "确认天气地点",
  setupDescription: "经纬度用于查询天气，以及在本地计算日出日落，无需填写城市名称。",
  settingsDescription: "经纬度用于查询天气，以及在本地计算日出日落，无需填写城市名称。",
  detect: "估算经纬度",
  detecting: "正在估算",
  detectHint: "根据公网 IP 估算城市级经纬度，结果可手动修正。",
  detected: (city: string | null) =>
    city ? `城市：${city}，已填入预估经纬度。` : "已填入预估经纬度，请核对。",
  detectionUnavailable: "无法连接到 ipapi.co。可在地图上查找地点坐标，再将纬度和经度分别填入下方。",
  manualHelp:
    "打开 OpenStreetMap，搜索所在地，在目标位置右键选择“显示地址”，从左侧复制纬度和经度；南纬和西经使用负数。",
  openMap: "打开地图查找坐标",
  latitudeLabel: "纬度",
  longitudeLabel: "经度",
  latitudePlaceholder: "-90 到 90",
  longitudePlaceholder: "-180 到 180",
  invalidLatitude: "纬度必须在 -90 到 90 之间。",
  invalidLongitude: "经度必须在 -180 到 180 之间。",
  requiredLatitude: "请填写纬度。",
  requiredLongitude: "请填写经度。",
};

const en = {
  title: "Confirm weather location",
  setupDescription:
    "Coordinates are used to request weather and calculate sunrise and sunset locally. No city name is needed.",
  settingsDescription:
    "Coordinates are used to request weather and calculate sunrise and sunset locally. No city name is needed.",
  detect: "Estimate coordinates",
  detecting: "Estimating",
  detectHint: "Estimate city-level coordinates from your public IP. You can correct the result manually.",
  detected: (city: string | null) =>
    city
      ? `City: ${city}. Estimated coordinates filled in.`
      : "Estimated coordinates filled in. Check that they are accurate.",
  detectionUnavailable:
    "Find your location on a map, then enter its latitude and longitude below, or retry after checking the issue.",
  manualHelp:
    "Open OpenStreetMap, search your location, right-click the point and choose Show address. Copy the latitude and longitude from the left panel; use negative values for south and west.",
  openMap: "Open map for coordinates",
  latitudeLabel: "Latitude",
  longitudeLabel: "Longitude",
  latitudePlaceholder: "-90 to 90",
  longitudePlaceholder: "-180 to 180",
  invalidLatitude: "Latitude must be between -90 and 90.",
  invalidLongitude: "Longitude must be between -180 and 180.",
  requiredLatitude: "Latitude is required.",
  requiredLongitude: "Longitude is required.",
};

export const LOCATION_COPY = { zh, en };
