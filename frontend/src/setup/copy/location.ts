const zh = {
  title: "地点",
  detect: "估算经纬度",
  detecting: "正在估算",
  detectHint: "按公网 IP 估算城市级坐标，可手动修正。",
  detected: (city: string | null) =>
    city ? `城市：${city}，已填入预估经纬度。` : "已填入预估经纬度，请核对。",
  detectionUnavailable: "无法连接到 ipapi.co。可在地图上查找地点坐标，再将纬度和经度分别填入下方。",
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
  title: "Location",
  detect: "Estimate coordinates",
  detecting: "Estimating",
  detectHint: "City-level estimate from your public IP. Adjust if needed.",
  detected: (city: string | null) =>
    city
      ? `City: ${city}. Estimated coordinates filled in.`
      : "Estimated coordinates filled in. Check that they are accurate.",
  detectionUnavailable:
    "Find your location on a map, then enter its latitude and longitude below, or retry after checking the issue.",
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
