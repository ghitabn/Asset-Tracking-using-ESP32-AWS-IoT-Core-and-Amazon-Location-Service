import { MapView } from "@aws-amplify/ui-react-geo";
import { NavigationControl } from "react-map-gl";
import Markers from "./components/Markers";
import LineOverlay from "./components/LineOverlay";
import useTracker from "./hooks/useTracker";

function App() {
  const [trackerPositions] = useTracker({
    DeviceId: "esp32-asset-01",
    TrackerName: "esp32-asset-01-tracker",
    EndTimeExclusive: new Date(),
    StartTimeInclusive: new Date(
      new Date().getTime() - 1000 * 60 * 60 * 24 * 30
    ),
  });

  return (
    <>
      <MapView
        initialViewState={{
          longitude: -73.804838,
          latitude: 45.492777,
          zoom: 12,
        }}
        style={{ width: "100vw", height: "100vh" }}
      >
        <NavigationControl showCompass={false} />
        <Markers trackerPositions={trackerPositions} />
        <LineOverlay trackerPositions={trackerPositions} />
      </MapView>
    </>
  );
}

export default App;
