import javax.jnlp.*;
import java.io.*;

public class PersistenceApp {

    public static void main(String[] args) {
        try {
            PersistenceService ps = (PersistenceService) ServiceManager.lookup("javax.jnlp.PersistenceService");
            BasicService bs = (BasicService) ServiceManager.lookup("javax.jnlp.BasicService");

            URL codebase = bs.getCodeBase();
            URL fileURL = new URL(codebase, "fp.txt");

            FileContents fc;
            try {
                fc = ps.get(fileURL);
                InputStream in = fc.getInputStream();
                BufferedReader reader = new BufferedReader(new InputStreamReader(in));
                String line = reader.readLine();
                System.out.println("Файл найден. Отпечаток: " + line);
            } catch (FileNotFoundException e) {
                // Файл не существует — создаем
                byte[] data = ("fp-" + System.currentTimeMillis()).getBytes();
                ps.create(fileURL, data.length);
                fc = ps.get(fileURL);
                OutputStream out = fc.getOutputStream(true);
                out.write(data);
                out.close();
                System.out.println("Файл создан. Отпечаток: " + new String(data));
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
