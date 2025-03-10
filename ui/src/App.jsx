import { useState, useEffect, useRef } from "react";

// npm install framer-motion
import { motion, AnimatePresence } from "framer-motion";

// npm install react-spinners
import { BarLoader } from "react-spinners";

// cd ui
// npm run dev


export default function App() {
  const [examples, setExamples] = useState([]);

  const [nextItem, setNextItem] = useState({});
  const hasRendered = useRef(false);
  const [dataProgress, setDataProgress] = useState(0);

  const [leftImages, setLeftImages] = useState([]);
  const [rightImages, setRightImages] = useState([]);
  const [droppedImages, setDroppedImages] = useState(new Set());

  const [isOpen, setIsOpen] = useState(false);
  const [evalResult, setEvalResult] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!hasRendered.current) {
      fetch("http://localhost:5000/api/examples")
        .then((response) => response.json())
        .then((data) => setExamples(data))
        .catch((error) => console.error("Error fetching examples:", error));
    }
  }, []);

  const fetchNextItem = () => {
    fetch("http://localhost:5000/api/next_item")
      .then((response) => response.json())
      .then((data) => {
        console.log("Next item, seen:", data.n_seen, "of", data.n_total)
        setNextItem({...data, key: data.n_seen});
        setDataProgress(Math.round(100 * nextItem.n_seen / nextItem.n_total));
      })
      .catch((error) => console.error("Error fetching data:", error));
  };

  const fetchEvaluation = async () => {
    setLoading(true); // Start loading
    try {
      const response = await fetch("http://localhost:5000/api/evaluation");
      const data = await response.json();
      setEvalResult({...data});
    } catch (error) {
      console.error("Error fetching evaluation:", error);
    }
    setLoading(false); // Stop loading
  };
  
  const handleEvaluationClick = async () => {
    await fetchEvaluation(); // Fetch data first
    setIsOpen(true); // Open the popup after image is ready
  };

  useEffect(() => {
    if (!hasRendered.current) {
      fetchNextItem();
      hasRendered.current = true;
    }
  }, []);

  const handleDrop = (event, side) => {
    event.preventDefault();
    const imageData = nextItem.image_base64;
    const identifier = nextItem.n_seen;

    if (droppedImages.has(identifier)) return;  // Prevent re-dropping

    if (side === "left") {
      setLeftImages([imageData, ...leftImages]);
    } else {
      setRightImages([imageData, ...rightImages]);
    }

    setDroppedImages(new Set([...droppedImages, identifier]))  // Mark as dropped
  };

  const allowDrop = (event) => {
    event.preventDefault();
  };

  const handleDragStart = (e, identifier) => {
    
    if (!droppedImages.has(identifier)) {
      e.dataTransfer.setData("text/plain", "image")
    } else {
      e.preventDefault(); // Prevent dragging if already dropped
    }
  };

  return (
    <div className="flex flex-col items-center p-4">

      <h1 className="text-2xl font-bold mb-4">Dekore Inspection Challenge</h1>
      
      <p className="mt-2 mb-4whitespace-pre-wrap">
        Can you beat the AI system in classifying the presented dekores correctly?<br />
        The system will present you with a series of images, and you have to classify them<br />
        via drag&drop into the correct list below. The example image will help you as reference.
      </p>

      <div className="flex justify-center gap-6 mt-6">
        {examples.map((example, index) => (
          <div key={index} className="flex flex-col items-center bg-gray-100 p-4 rounded-lg shadow-lg">
            <img src={example.image_base64} alt={example.label} className="w-[128px] h-[128px] object-cover rounded" />
            <h2 className="mt-2 text-lg font-semibold">{example.label}</h2>
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm mt-4 p-4 rounded-full">
        <div
          className="bg-blue-500 text-xs text-center text-white p-1 rounded-full"
          style={{ width: `${dataProgress}%` }}
        >
          {dataProgress}%
        </div>
      </div>

      <div className="flex gap-4">  
        <button
          onClick={fetchNextItem}
          className="px-4 py-2 bg-blue-500 text-white rounded shadow-lg hover:bg-blue-600"
        >
          Next Image
        </button>

        <button
          onClick={handleEvaluationClick}
          className="px-4 py-2 bg-blue-500 text-white rounded shadow-lg hover:bg-blue-600"
        >
          Evaluate Decisions
        </button>
      </div>

      {loading && (  // Loading spinner
        <div className="flex justify-center items-center mt-4">
          <BarLoader color="#3b82f6" size={15} />
          <p className="ml-4">Loading Evaluation...</p>
        </div>
      )}
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-white p-6 rounded-lg shadow-lg max-w-sm text-center"

              // Slide down effect
              // initial={{ y: -50, opacity: 0 }}
              // animate={{ y: 0, opacity: 1 }}
              // exit={{ y: -50, opacity: 0 }}

              // Zoom in and out effect
              // initial={{ scale: 0.8, opacity: 0 }}
              // animate={{ scale: 1, opacity: 1 }}
              // exit={{ scale: 0.8, opacity: 0 }}

              // Rotate effect: rotateX, rotateY, rotateZ
              initial={{ rotateZ: -360, opacity: 0 }}
              animate={{ rotateZ: 0, opacity: 1 }}
              exit={{ rotateZ: -360, opacity: 0 }}

              transition={{ duration: 0.5 }}
            >
              <h2 className="text-xl font-semibold mb-2">Evaluation Results</h2>
              <div className="flex justify-center items-center">
                  <img
                    src={evalResult.image_base64}
                    alt="Confusion Matrix"
                    className="rounded-lg mb-4"
                  />
              </div>
              <p className="mb-4">The accuracy of the AI system is: {evalResult.acc}</p>
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 bg-red-500 text-white rounded shadow-lg hover:bg-red-600"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {nextItem.image_base64 && (
        <img
          key={nextItem.key}
          src={nextItem.image_base64}
          alt="Draggable"
          className="rounded shadow-lg mt-4 cursor-grab"
          draggable="true"
          onDragStart={(e) => handleDragStart(e, nextItem.n_seen)}
        />
      )}

      <div className="flex w-full max-w-4xl gap-4 justify-center">
        <div
          className="w-[200px] min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "left")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">
            {examples.length > 0 ? `${examples[0].label} Images` : "Loading..."}
          </h2>
          {leftImages.map((img, key) => (
            <img
              key={key}
              src={img}
              alt="Dropped"
              className="w-[128px] h-[128px] mb-2 rounded shadow-lg"
            />
          ))}
        </div>
        <div
          className="w-[200px] min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "right")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">
            {examples.length > 0 ? `${examples[1].label} Images` : "Loading..."}
          </h2>
          {rightImages.map((img, key) => (
            <img
              key={key}
              src={img}
              alt="Dropped"
              className="w-[128px] h-[128px] mb-2 rounded shadow-lg"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
