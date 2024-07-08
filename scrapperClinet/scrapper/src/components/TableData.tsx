import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Paper from "@mui/material/Paper";
import { IRecord } from "../interfaces/record.interface";

// const rows = [createData("Frozen yoghurt", 159, 6.0, 24, 4.0)];

const TableData = ({ records }: { record: IRecord[] }) => {
  return (
    <TableContainer
      component={Paper}
      className="max-w-5xl m-auto border-4 border-white "
    >
      <Table sx={{ minWidth: 650 }} size="small" aria-label="a dense table">
        <TableHead style={{ borderBottom: "2px solid black" }}>
          <TableRow
            className="border-b-2 border-black bg-white font-bold"
            style={{ borderBottom: "2px solid black" }}
          >
            <TableCell style={{ fontWeight: "bold" }}>S.No</TableCell>

            <TableCell style={{ fontWeight: "bold" }}>
              Company LinkedIn URL
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
              Company Name
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
              Company URL
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
              Designation
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
              Job Title
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
              Location
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
              Person LinkedIn URL
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
              Person Name
            </TableCell>
            <TableCell style={{ fontWeight: "bold" }} align="right">
            Email
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {records?.length > 0 && 
            records?.map((row: IRecord, index:number) => (
              <TableRow
                key={index}
                sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
                className={`${index % 2 == 0 && "bg-gray-100"}`}
              >
                <TableCell component="th" scope="row">
                  {index + 1}
                </TableCell>
                <TableCell  component="th" scope="row">
                  <a target="_blank" href={row["Company LinkedIn URL"]}>
                  {row["Company LinkedIn URL"]}
                  </a>
                </TableCell>
                <TableCell align="right">{row["Company Name"]}</TableCell>
                <TableCell component="th" scope="row">
                  {row["Company URL"]}
                </TableCell>
                <TableCell align="right">{row["Designation"]}</TableCell>
                <TableCell align="right">{row["Job Title"]}</TableCell>
                <TableCell align="right">{row["Location"]}</TableCell>
                <TableCell align="right">{row["Person LinkedIn URL"]}</TableCell>
                <TableCell align="right">{row["Person Name"]}</TableCell>
                <TableCell align="right">{row["Email"]}</TableCell>

              </TableRow>
            ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
export default TableData;
