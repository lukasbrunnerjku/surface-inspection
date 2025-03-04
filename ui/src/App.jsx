import { useEffect, useState } from "react";
// import './App.css'
// the above css file is not needed anymore for now

// cd ui
// npm run dev


export default function App() {
  const [data, setData] = useState({ text: "", image_base64: "" });
  const [progress, setProgress] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [leftImages, setLeftImages] = useState([]);
  const [rightImages, setRightImages] = useState([]);

  const fetchImageAndText = () => {
    fetch("http://localhost:5000/api/data")
      .then((response) => response.json())
      .then((data) => {
        console.log("Fetched new image with index:", data.index)
        setData({...data, key: data.index});  // Use key to prevent caching
      })
      .catch((error) => console.error("Error fetching data:", error));
  };

  const startProcessing = () => {
    setProcessing(true);
    setProgress(0);

    const eventSource = new EventSource("http://localhost:5000/api/process");

    eventSource.onmessage = (event) => {
      const progressData = JSON.parse(event.data);
      setProgress(progressData.progress);

      if (progressData.progress === 100) {
        eventSource.close();
        setProcessing(false);
        fetchImageAndText(); // Fetch new image after processing
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setProcessing(false);
    };
  };

  const handleDrop = (event, side) => {
    event.preventDefault();
    const imageData = data.image_base64;
    // [...leftImages, imageData] adds image to bottom of drag and drop
    // [imageData, ...leftImages] adds to top
    if (side === "left") {
      setLeftImages([imageData, ...leftImages]);
    } else {
      setRightImages([imageData, ...rightImages]);
    }
  };

  const allowDrop = (event) => {
    event.preventDefault();
  };

  return (
    <div className="flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold mb-4">Flask & React Drag and Drop</h1>
      <button
        onClick={startProcessing}
        disabled={processing}
        className="bg-blue-500 text-white px-4 py-2 rounded shadow mt-4"
      >
        {processing ? "Processing..." : "Start Processing"}
      </button>
      {processing && (
        <div className="w-full max-w-sm mt-4 bg-gray-200 rounded-full">
          <div
            className="bg-blue-500 text-xs text-center text-white p-1 rounded-full"
            style={{ width: `${progress}%` }}
          >
            {progress}%
          </div>
        </div>
      )}
      {data.image_base64 && (
        <img
          key={data.key}
          src={data.image_base64}
          alt="Draggable"
          className="rounded shadow-lg mt-4 cursor-grab"
          draggable="true"
          onDragStart={(e) => e.dataTransfer.setData("text/plain", "image")}
        />
      )}
      {data.text && <p className="mb-4 text-lg">{data.text}</p>}
      <div className="flex w-full max-w-4xl gap-4">
        <div
          className="w-1/2 min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "left")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">Left Area</h2>
          {leftImages.map((img, index) => (
            <img key={index} src={img} alt="Dropped" className="w-[128px] h-[128px] mb-2 rounded shadow-lg" />
          ))}
        </div>
        <div
          className="w-1/2 min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "right")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">Right Area</h2>
          {rightImages.map((img, index) => (
            <img key={index} src={img} alt="Dropped" className="w-[128px] h-[128px] mb-2 rounded shadow-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}


// export default function App() {
//   const [data, setData] = useState({ text: "", image_base64: "" });
//   const [progress, setProgress] = useState(0);
//   const [processing, setProcessing] = useState(false);

//   const fetchImageAndText = () => {
//     fetch("http://localhost:5000/api/data")
//       .then((response) => response.json())
//       .then((data) => setData(data))
//       .catch((error) => console.error("Error fetching data:", error));
//   };

//   const startProcessing = () => {
//     setProcessing(true);
//     setProgress(0);

//     const eventSource = new EventSource("http://localhost:5000/api/process");

//     eventSource.onmessage = (event) => {
//       const progressData = JSON.parse(event.data);
//       setProgress(progressData.progress);

//       if (progressData.progress === 100) {
//         eventSource.close();
//         setProcessing(false);
//         fetchImageAndText(); // Fetch new image after processing
//       }
//     };

//     eventSource.onerror = () => {
//       eventSource.close();
//       setProcessing(false);
//     };
//   };

//   return (
//     <div className="flex flex-col items-center p-4">
//       <h1 className="text-2xl font-bold mb-4">Flask & React Image Viewer with Progress</h1>
//       {data.text && <p className="mb-4 text-lg">{data.text}</p>}
//       {data.image_base64 && (
//         <img src={data.image_base64} alt="Fetched from backend" className="rounded shadow-lg mb-4" />
//       )}
//       <button
//         onClick={startProcessing}
//         disabled={processing}
//         className="bg-blue-500 text-white px-4 py-2 rounded shadow"
//       >
//         {processing ? "Processing..." : "Start Processing"}
//       </button>
//       {processing && (
//         <div className="w-full max-w-sm mt-4 bg-gray-200 rounded-full">
//           <div
//             className="bg-blue-500 text-xs text-center text-white p-1 rounded-full"
//             style={{ width: `${progress}%` }}
//           >
//             {progress}%
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }


// export default function App() {
//   const [progress, setProgress] = useState(0);
//   const [processing, setProcessing] = useState(false);

//   const startProcessing = () => {
//     setProcessing(true);
//     setProgress(0);

//     const eventSource = new EventSource("http://localhost:5000/api/process");

//     eventSource.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       setProgress(data.progress);

//       if (data.progress === 100) {
//         eventSource.close();
//         setProcessing(false);
//       }
//     };

//     eventSource.onerror = () => {
//       eventSource.close();
//       setProcessing(false);
//     };
//   };

//   return (
//     <div className="flex flex-col items-center p-4">
//       <h1 className="text-2xl font-bold mb-4">Flask & React Progress Bar</h1>
//       <button
//         onClick={startProcessing}
//         disabled={processing}
//         className="bg-blue-500 text-white px-4 py-2 rounded shadow"
//       >
//         Start Processing
//       </button>

//       {processing && (
//         <div className="w-full max-w-sm mt-4 bg-gray-200 rounded-full">
//           <div
//             className="bg-blue-500 text-xs text-center text-white p-1 rounded-full"
//             style={{ width: `${progress}%` }}
//           >
//             {progress}%
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

// export default function App() {
//   const [data, setData] = useState({ text: "", image_base64: "" });

//   useEffect(() => {
//     fetch("http://localhost:5000/api/data")
//       .then((response) => response.json())
//       .then((data) => setData(data))
//       .catch((error) => console.error("Error fetching data:", error));
//   }, []);

//   return (
//     <div className="flex flex-col items-center p-4">
//       <h1 className="text-2xl font-bold mb-4">Flask & React Image Viewer</h1>
//       {data.text && <p className="mb-4 text-lg">{data.text}</p>}
//       {data.image_base64 && (
//         <img src={data.image_base64} alt="Fetched from backend" className="rounded shadow-lg" />
//       )}
//     </div>
//   );
// }
