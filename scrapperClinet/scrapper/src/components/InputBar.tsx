import SearchIcon from "@mui/icons-material/Search";
import { Box, Input, InputAdornment, Typography } from "@mui/material";
import CircularProgress from "@mui/material/CircularProgress";

interface InputBarProps {
  value: string;
  handleChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleData: () => void;
  loading: boolean;
  handleCancelRequest: () => void;
}

const InputBar = ({
  value,
  handleChange,
  handleData,
  loading,
  handleCancelRequest,
}: InputBarProps) => {
  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      handleData();
    }
  };
  return (
    <Box className=" flex-row items-center  flex justify-between">
      {/* <Typography>LinkMiner</Typography> */}

      <Box
        className=" border border-gray-500 rounded-full overflow-hidden  text-white  "
        style={{ boxShadow: "1px 1px 5px 3px rgba(245,236,236,0.75)" }}
      >
        <Input
          fullWidth
          value={value}
          onChange={handleChange}
          style={{ color: "white" }}
          onKeyPress={handleKeyPress}
          className="pl-5 placeholder:text-white text-white"
          endAdornment={
            <InputAdornment position="start">
              <Box className="border-l pl-2 border-gray-500">
                {loading ? (
                  <CircularProgress
                    size={14}
                    className=" cursor-pointer"
                    onClick={handleCancelRequest}
                    style={{ color: "white" }}
                  />
                ) : (
                  <SearchIcon
                    onClick={handleData}
                    style={{ color: "white" }}
                    className=" cursor-pointer"
                  />
                )}
              </Box>
            </InputAdornment>
          }
        />
      </Box>
    </Box>
  );
};

export default InputBar;
