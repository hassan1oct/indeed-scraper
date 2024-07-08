import { ChangeEvent, useEffect, useRef, useState } from "react";
import InputBar from "./components/InputBar";
import TableData from "./components/TableData";
import { Box } from "@mui/material";
import { io } from "socket.io-client";


const App = () => {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [newRecords, setRecords] = useState<any[]>([]);
  const [ioInstance, setIoInstance] = useState<any>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  let link = "https://www.indeed.com/jobs?q=node+js+developer";

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  };

  const startScraping = async () => {
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;
    try {
      const res = await fetch("http://localhost:5000/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ indeed_page: value }),
        signal,
      });

      const data = await res.json();
      setResponse(data);
      console.log("Scraping completed");
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleData = () => {
    setLoading(true);
    startScraping();
    setValue("");
  };

  const handleCancelRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  useEffect(() => {
    const socket = io("http://localhost:5000");
    console.log(socket, "-->");
    setIoInstance(socket);

    socket.on("connect", () => {
      console.log("Connected to Socket.IO server");
    });

    socket.on("disconnect", () => {
      console.log("Disconnected from Socket.IO server");
    });

    return () => {
      socket.off("connect");
      socket.off("new_record");
      socket.off("disconnect");
      socket.disconnect();
      socket.close();
    };
  }, []);

  useEffect(() => {
    if (ioInstance) {
      ioInstance.on("error", (error) => {
        console.log("Socket.IO error:", error);
      });

      ioInstance.on("new_record", (record: any) => {
        console.log("New record received:", record);
        
        setRecords((prevRecords) => [...prevRecords, record]);
      });
    }
  }, [ioInstance]);
  console.log(newRecords, "newrec");

  return (
    <div className=" bg-black flex flex-col text-white gap-10 py-10 h-[100vh]">
      <Box className="max-w-5xl mx-auto">
        <InputBar
          value={value}
          handleChange={handleChange}
          handleData={handleData}
          loading={loading}
          handleCancelRequest={handleCancelRequest}
        />
      </Box>
      <TableData records={newRecords} /> {/* Pass records to TableData */}
    </div>
  );
};

export default App;
